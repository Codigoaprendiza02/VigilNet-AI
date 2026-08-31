import random
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sdv.sampling import Condition
from app.agents.base import BaseAgent, CampaignStep
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

CARD_TESTER_SYSTEM_INSTRUCTION = """
You are an AI Red Team agent simulating the "Card Tester" payment fraud persona.
Your objective is to validate stolen credit card numbers by initiating a series of transactions.

Your planning profile:
- Start with very small value transactions (e.g., $1.00 - $5.00) to verify if the card is active and has available balance without triggering standard high-value alert thresholds.
- Vary the merchant categories (retail, grocery, online_gaming, gas_station) to mimic normal cardholder activity.
- Step up the transaction value gradually if the initial low-value checks are successful.
- Use realistic timing/spacing delays (spacing_seconds) between steps (e.g., 60 to 600 seconds) to avoid trigger-happy rate limits.
- Provide a brief logical rationale for each step explaining why this pattern helps bypass basic, static fraud-detection rules.
"""

class CardTesterAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="card_tester",
            system_instruction=CARD_TESTER_SYSTEM_INSTRUCTION
        )

    async def act(self, step_plan: CampaignStep, round_id: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Execute a planned campaign step by projecting it through the PaySim CTGAN generator."""
        logger.info(f"[CardTester] Executing step {step_plan.step_number} ({step_plan.transaction_type} of ${step_plan.amount})")
        
        # Load the PaySim synthesizer
        synthesizer = self.load_synthesizer("paysim")
        
        tx_type = step_plan.transaction_type.upper()
        if tx_type not in ['PAYMENT', 'TRANSFER', 'CASH_OUT', 'CASH_IN', 'DEBIT']:
            tx_type = 'PAYMENT'
            
        synthetic_row = {}
        
        # Try to sample conditionally
        try:
            condition = Condition(
                column_values={'type': tx_type, 'isFraud': 1},
                num_rows=1
            )
            synthetic_df = synthesizer.sample_from_conditions(conditions=[condition])
            if not synthetic_df.empty:
                synthetic_row = synthetic_df.iloc[0].to_dict()
        except Exception as e:
            logger.warning(f"Conditional sampling failed: {e}. Falling back to standard sample & filter.")
            
        # Fallback: standard sample and filter
        if not synthetic_row:
            try:
                synthetic_df = synthesizer.sample(num_rows=100)
                filtered = synthetic_df[synthetic_df['type'] == tx_type]
                if not filtered.empty:
                    synthetic_row = filtered.iloc[0].to_dict()
                else:
                    synthetic_row = synthetic_df.iloc[0].to_dict()
            except Exception as sample_err:
                logger.error(f"Fallback sampling failed: {sample_err}. Creating default statistical values.")
                # Hardcoded fallback values representing realistic statistics
                synthetic_row = {
                    'oldbalanceOrg': 1000.0,
                    'newbalanceOrig': 1000.0 - step_plan.amount,
                    'oldbalanceDest': 500.0,
                    'newbalanceDest': 500.0 + step_plan.amount
                }

        # Pin the card to be identical for all steps in this round to simulate testing the same card
        import hashlib
        h = hashlib.md5(round_id.encode('utf-8')).hexdigest()
        name_orig = f"C{int(h[:8], 16) % 9000000000 + 1000000000}"
        
        # Destination is merchant ('M' + 10 digits) if type is PAYMENT, otherwise customer ('C')
        if tx_type == 'PAYMENT':
            name_dest = f"M{random.randint(1000000000, 9999999999)}"
        else:
            name_dest = f"C{random.randint(1000000000, 9999999999)}"

        # Construct the final event document
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
            logger.info(f"[CardTester] Successfully persisted event {event_doc['event_id']} to MongoDB.")
        except Exception as mongo_err:
            logger.error(f"Failed to persist event to MongoDB: {mongo_err}")
            # We don't crash, we still return the document for testing/logging
            
        return event_doc
