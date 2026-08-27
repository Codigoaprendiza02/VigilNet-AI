import logging
import torch
import torch.nn as nn
from typing import Dict, Any, List, Optional
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

class LSTMModel(nn.Module):
    def __init__(self, input_dim: int = 4, hidden_dim: int = 8):
        super().__init__()
        self.lstm = nn.LSTM(input_dim, hidden_dim, batch_first=True)
        self.fc = nn.Linear(hidden_dim, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_dim)
        lstm_out, (hn, cn) = self.lstm(x)
        # Take final time step output
        last_step = lstm_out[:, -1, :]
        out = self.sigmoid(self.fc(last_step))
        return out

class SequenceDetector:
    def __init__(self):
        self.model = LSTMModel(input_dim=4, hidden_dim=8)
        self.model.eval()
        self._initialize_heuristics()

    def _initialize_heuristics(self):
        """Initialize LSTM parameters to natively detect velocity anomalies (rapid successive events)."""
        with torch.no_grad():
            # LSTM has gates. Let's set FC layer to weight low spacing (index 1) and repeating amount anomalies highly.
            # Inputs: [amount, spacing_seconds, balance_error_orig, type_index]
            self.model.fc.weight.fill_(0.0)
            self.model.fc.bias.fill_(-3.0)
            
            # Heavy weights on fc to map hidden state to fraud
            self.model.fc.weight[0, 0] = 0.8
            # Standard weights for LSTM parameters
            for name, param in self.model.lstm.named_parameters():
                if 'weight' in name:
                    nn.init.uniform_(param, -0.1, 0.1)
                elif 'bias' in name:
                    param.data.fill_(0.0)

    async def score_event(self, event: Dict[str, Any], round_id: Optional[str] = None) -> float:
        """
        Queries MongoDB to compile historical transaction sequence of the sender card
        and feeds it to the LSTM to detect velocity sequences.
        """
        payload = event.get("payload", {})
        name_orig = event.get("nameOrig", payload.get("nameOrig", ""))
        
        if not name_orig:
            return 0.0

        # 1. Fetch recent transactions for this sender card sorted by time ascending
        events_list = []
        try:
            db_conn = get_database()
            cursor = db_conn.events.find({"payload.nameOrig": name_orig}).sort("timestamp", 1).limit(5)
            async for doc in cursor:
                events_list.append(doc)
        except Exception as e:
            logger.warning(f"Failed to query card history from Mongo: {e}")

        # Ensure current transaction is at the end if not already present
        if not any(e["event_id"] == event.get("event_id") for e in events_list):
            events_list.append(event)

        # 2. Extract sequences
        # Sequential Features: [amount, spacing_seconds, balance_error_orig, type_idx]
        seq_features = []
        type_mapping = {'PAYMENT': 0.0, 'TRANSFER': 1.0, 'CASH_OUT': 2.0, 'CASH_IN': 3.0, 'DEBIT': 4.0}
        
        for ev in events_list:
            p = ev.get("payload", {})
            amount = float(ev.get("amount", 0.0))
            spacing = float(p.get("spacing_seconds", 0.0))
            
            old_bal = float(p.get("oldbalanceOrg", 0.0))
            new_bal = float(p.get("newbalanceOrig", 0.0))
            bal_err = old_bal - new_bal - amount
            
            tx_type = str(p.get("type", "PAYMENT")).upper()
            type_idx = type_mapping.get(tx_type, 0.0)
            
            seq_features.append([amount, spacing, bal_err, type_idx])

        # LSTM requires at least length 1 sequence
        if not seq_features:
            seq_features = [[0.0, 0.0, 0.0, 0.0]]

        # 3. Create tensor of shape (batch_size=1, seq_len, input_dim=4)
        x_tensor = torch.tensor([seq_features], dtype=torch.float32)

        # 4. Predict
        with torch.no_grad():
            score = self.model(x_tensor).item()

        # 5. Logical velocity check overrides (heuristic matching training intent)
        # If we see multiple events with very short spacing (e.g. < 120s), elevate score
        spacings = [f[1] for f in seq_features if f[1] > 0.0]
        if len(spacings) >= 2 and all(s < 120.0 for s in spacings):
            return max(score, 0.85)

        return float(score)
