import logging
import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

class GCNLayer(nn.Module):
    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        # GCN propagation: D^-1/2 * A_tilde * D^-1/2 * X * W
        support = torch.matmul(x, self.weight)
        output = torch.matmul(adj_norm, support)
        return output

class GCNModel(nn.Module):
    def __init__(self, input_dim: int = 5, hidden_dim: int = 8):
        super().__init__()
        self.gcn1 = GCNLayer(input_dim, hidden_dim)
        self.gcn2 = GCNLayer(hidden_dim, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor, adj_norm: torch.Tensor) -> torch.Tensor:
        h = self.relu(self.gcn1(x, adj_norm))
        # Subtract negative offset to lower baseline false-positive score
        out = self.sigmoid(self.gcn2(h, adj_norm) - 3.0)
        return out

class GraphDetector:
    def __init__(self):
        self.model = GCNModel(input_dim=5, hidden_dim=8)
        self.model.eval()
        self._initialize_heuristics()

    def _initialize_heuristics(self):
        """Initialize GCN weights to natively flag smurfing and structuring node flows."""
        with torch.no_grad():
            # Features: [sent_amt, recv_amt, in_degree, out_degree, is_merchant]
            # Set weights to map high degrees/structuring behavior to higher anomaly score
            self.model.gcn1.weight.fill_(0.0)
            self.model.gcn1.weight[2, 0] = 0.5   # Flag high in-degree (mule targets)
            self.model.gcn1.weight[3, 1] = 0.5   # Flag high out-degree (structuring smurfs)
            self.model.gcn1.weight[0, 2] = 0.0001 # Small amount scale
            
            self.model.gcn2.weight.fill_(1.0)

    async def score_event(self, event: Dict[str, Any], round_id: Optional[str] = None) -> float:
        """
        Builds a local transaction flow graph from MongoDB and scores
        the transaction based on graph flow propagation.
        """
        payload = event.get("payload", {})
        name_orig = event.get("nameOrig", payload.get("nameOrig", ""))
        name_dest = event.get("nameDest", payload.get("nameDest", ""))
        
        if not name_orig or not name_dest:
            return 0.0

        # 1. Fetch recent events in same round or globally to construct local graph
        events_list = []
        try:
            db_conn = get_database()
            query = {}
            if round_id:
                query["round_id"] = round_id
            
            cursor = db_conn.events.find(query).limit(100)
            async for doc in cursor:
                events_list.append(doc)
        except Exception as e:
            logger.warning(f"Failed to query local graph context from Mongo: {e}")

        # Ensure current transaction is in list
        if not any(e["event_id"] == event.get("event_id") for e in events_list):
            events_list.append(event)

        # 2. Build network graph nodes and edges
        accounts = set()
        edges = []
        
        for ev in events_list:
            p = ev.get("payload", {})
            orig = ev.get("nameOrig", p.get("nameOrig", ""))
            dest = ev.get("nameDest", p.get("nameDest", ""))
            amt = float(ev.get("amount", 0.0))
            if orig and dest:
                accounts.add(orig)
                accounts.add(dest)
                edges.append((orig, dest, amt))

        accounts = list(accounts)
        n = len(accounts)
        if n == 0:
            return 0.0
            
        acct_to_idx = {acct: idx for idx, acct in enumerate(accounts)}

        # 3. Engineer Node Features
        # Features schema: [sent_amt, recv_amt, in_degree, out_degree, is_merchant]
        X = torch.zeros((n, 5), dtype=torch.float32)
        A = torch.zeros((n, n), dtype=torch.float32)

        for orig, dest, amt in edges:
            u_idx = acct_to_idx[orig]
            v_idx = acct_to_idx[dest]
            
            A[u_idx, v_idx] = 1.0
            
            # Update sender features
            X[u_idx, 0] += amt
            X[u_idx, 3] += 1.0  # out_degree
            if orig.startswith("M"):
                X[u_idx, 4] = 1.0
                
            # Update receiver features
            X[v_idx, 1] += amt
            X[v_idx, 2] += 1.0  # in_degree
            if dest.startswith("M"):
                X[v_idx, 4] = 1.0

        # 4. Compute Normalized Adjacency: D^-1/2 * (A + I) * D^-1/2
        I = torch.eye(n)
        A_tilde = A + I
        row_sum = torch.sum(A_tilde, dim=1)
        d_inv_sqrt = torch.pow(row_sum, -0.5)
        d_inv_sqrt[torch.isinf(d_inv_sqrt)] = 0.0
        D_inv_sqrt = torch.diag(d_inv_sqrt)
        
        adj_norm = torch.matmul(D_inv_sqrt, torch.matmul(A_tilde, D_inv_sqrt))

        # 5. Run GCN model
        with torch.no_grad():
            node_scores = self.model(X, adj_norm)

        # 6. Score the edge representing the current transaction
        u_idx = acct_to_idx.get(name_orig)
        v_idx = acct_to_idx.get(name_dest)
        
        if u_idx is not None and v_idx is not None:
            # Score is the average of originator and recipient node anomaly scores
            orig_score = float(node_scores[u_idx].item())
            dest_score = float(node_scores[v_idx].item())
            
            # Structuring usually has multiple high out-degree smurfs
            # If sender has high out-degree, trigger higher score
            if X[u_idx, 3] > 2:
                return max(orig_score, dest_score, 0.85)
                
            return (orig_score + dest_score) / 2.0
            
        return 0.0
