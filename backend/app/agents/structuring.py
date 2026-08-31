import random
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sdv.sampling import Condition
from app.agents.base import BaseAgent, CampaignStep
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

STRUCTURING_SYSTEM_INSTRUCTION = """
You are an AI Red Team agent simulating the "Structuring / Smurfing" money laundering persona.
Your objective is to break down a large illicit sum of money (e.g. $50,000) into a series of smaller transactions, all kept strictly under standard cash transaction reporting thresholds (such as $10,000) to avoid automatic flagging.

Your planning profile:
- Generate transactions valued between $7,500 and $9,500.
- Primarily utilize TRANSFER or CASH_OUT transaction types to simulate shifting funds across shell accounts.
- Space transactions at modest intervals (e.g., 300 to 1800 seconds) to avoid high-frequency velocity alert triggers.
"""

class StructuringAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="structuring",
            system_instruction=STRUCTURING_SYSTEM_INSTRUCTION
        )

    async def act(self, step_plan: CampaignStep, round_id: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Execute campaign step by projecting it through the PaySim CTGAN generator."""
        logger.info(f"[Structuring] Executing step {step_plan.step_number} ({step_plan.transaction_type} of ${step_plan.amount})")
        
        # Load the PaySim synthesizer
        synthesizer = self.load_synthesizer("paysim")
        
        tx_type = step_plan.transaction_type.upper()
        if tx_type not in ['PAYMENT', 'TRANSFER', 'CASH_OUT', 'CASH_IN', 'DEBIT']:
            tx_type = 'TRANSFER'
            
        synthetic_row = {}
        
        try:
            condition = Condition(
                column_values={'type': tx_type, 'isFraud': 1},
                num_rows=1
            )
            synthetic_df = synthesizer.sample_from_conditions(conditions=[condition])
            if not synthetic_df.empty:
                synthetic_row = synthetic_df.iloc[0].to_dict()
        except Exception as e:
            logger.warning(f"Structuring conditional sampling failed: {e}. Falling back to standard sample.")

        if not synthetic_row:
            try:
                synthetic_df = synthesizer.sample(num_rows=100)
                filtered = synthetic_df[synthetic_df['type'] == tx_type]
                if not filtered.empty:
                    synthetic_row = filtered.iloc[0].to_dict()
                else:
                    synthetic_row = synthetic_df.iloc[0].to_dict()
            except Exception as sample_err:
                logger.error(f"Fallback sampling failed: {sample_err}. Creating defaults.")
                synthetic_row = {
                    'oldbalanceOrg': 25000.0,
                    'newbalanceOrig': 25000.0 - step_plan.amount,
                    'oldbalanceDest': 1000.0,
                    'newbalanceDest': 1000.0 + step_plan.amount
                }

        # Pin the origin account to be identical for all steps in this round to simulate structuring from a single origin
        import hashlib
        h = hashlib.md5(round_id.encode('utf-8')).hexdigest()
        name_orig = f"C{int(h[:8], 16) % 9000000000 + 1000000000}"
        
        if tx_type == 'PAYMENT':
            name_dest = f"M{random.randint(1000000000, 9999999999)}"
        else:
            name_dest = f"C{random.randint(1000000000, 9999999999)}"

        # Construct final event doc
        event_doc = {
            "event_id": str(uuid.uuid4()),
            "round_id": round_id,
            "persona": self.name,
            "timestamp": datetime.utcnow() + timedelta(seconds=step_plan.spacing_seconds),
            "amount": float(step_plan.amount),
            "merchant_category": step_plan.merchant_category,
            "is_synthetic_attack": True,
            "payload": {
                "type": tx_type,
                "oldbalanceOrg": float(synthetic_row.get('oldbalanceOrg', 0.0)),
                "newbalanceOrig": float(synthetic_row.get('newbalanceOrig', 0.0)),
                "oldbalanceDest": float(synthetic_row.get('oldbalanceDest', 0.0)),
                "newbalanceDest": float(synthetic_row.get('newbalanceDest', 0.0)),
                "nameOrig": name_orig,
                "nameDest": name_dest,
                "spacing_seconds": step_plan.spacing_seconds,
                "rationale": step_plan.rationale,
                "step_number": step_plan.step_number
            },
            "detection_result": None
        }

        # Persist to MongoDB
        try:
            db_conn = get_database()
            await db_conn.events.insert_one(event_doc)
            logger.info(f"[Structuring] Persisted event {event_doc['event_id']} to MongoDB.")
        except Exception as mongo_err:
            logger.error(f"Failed to persist event: {mongo_err}")
            
        return event_doc
