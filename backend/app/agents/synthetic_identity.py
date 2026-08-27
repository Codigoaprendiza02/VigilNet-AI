import random
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sdv.sampling import Condition
from app.agents.base import BaseAgent, CampaignStep
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

SYNTHETIC_IDENTITY_SYSTEM_INSTRUCTION = """
You are an AI Red Team agent simulating the "Synthetic Identity Fraud" persona.
Your objective is to open accounts and execute transaction campaigns using a hybrid identity (combining real and fake credit profiles).

Your planning profile:
- Simulate credit card transactions of moderate to large value ($20 to $400) to maximize extraction.
- Choose merchant categories like retail, electronics, and travel to establish cardholder profiles.
- Keep transaction spacing variable (e.g. 120 to 1800 seconds) to look like real cardholder behavior.
- Conforms to standard transaction types like PAYMENT or TRANSFER.
"""

class SyntheticIdentityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="synthetic_identity",
            system_instruction=SYNTHETIC_IDENTITY_SYSTEM_INSTRUCTION
        )

    async def act(self, step_plan: CampaignStep, round_id: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Execute campaign step by projecting it through the IEEE-CIS CTGAN model."""
        logger.info(f"[SyntheticIdentity] Executing step {step_plan.step_number} ({step_plan.transaction_type} of ${step_plan.amount})")
        
        # Load IEEE-CIS Synthesizer
        synthesizer = self.load_synthesizer("ieee")
        
        # Map transaction_type to IEEE-CIS ProductCD
        # ProductCD: W (web), H (hood/housing), R (retail), M (mail), etc.
        product_cd = 'W'
        if step_plan.transaction_type == 'TRANSFER':
            product_cd = 'R'
        elif step_plan.transaction_type == 'DEBIT':
            product_cd = 'H'

        synthetic_row = {}
        
        try:
            condition = Condition(
                column_values={'ProductCD': product_cd, 'isFraud': 1},
                num_rows=1
            )
            synthetic_df = synthesizer.sample_from_conditions(conditions=[condition])
            if not synthetic_df.empty:
                synthetic_row = synthetic_df.iloc[0].to_dict()
        except Exception as e:
            logger.warning(f"IEEE conditional sampling failed: {e}. Falling back to standard sample & filter.")

        if not synthetic_row:
            try:
                synthetic_df = synthesizer.sample(num_rows=100)
                filtered = synthetic_df[synthetic_df['ProductCD'] == product_cd]
                if not filtered.empty:
                    synthetic_row = filtered.iloc[0].to_dict()
                else:
                    synthetic_row = synthetic_df.iloc[0].to_dict()
            except Exception as sample_err:
                logger.error(f"IEEE fallback sampling failed: {sample_err}. Creating defaults.")
                synthetic_row = {
                    'card1': float(random.randint(1000, 20000)),
                    'card2': float(random.randint(100, 600)),
                    'card4': random.choice(['visa', 'mastercard']),
                    'card6': random.choice(['debit', 'credit'])
                }

        # Build synthetic identity details
        card1 = float(synthetic_row.get('card1', random.randint(1000, 20000)))
        card2 = float(synthetic_row.get('card2', random.randint(100, 600)))
        card4 = str(synthetic_row.get('card4', 'visa'))
        card6 = str(synthetic_row.get('card6', 'debit'))

        # Construct final event doc
        # We populate PaySim equivalents to keep scoring robust
        event_doc = {
            "event_id": str(uuid.uuid4()),
            "round_id": round_id,
            "persona": self.name,
            "timestamp": datetime.utcnow() + timedelta(seconds=step_plan.spacing_seconds),
            "amount": float(step_plan.amount),
            "merchant_category": step_plan.merchant_category,
            "is_synthetic_attack": True,
            "payload": {
                "type": step_plan.transaction_type,
                # PaySim equivalents for tabular scorer fallback
                "oldbalanceOrg": 5000.0,
                "newbalanceOrig": 5000.0 - step_plan.amount,
                "oldbalanceDest": 10000.0,
                "newbalanceDest": 10000.0 + step_plan.amount,
                "nameOrig": f"C{random.randint(1000000000, 9999999999)}",
                "nameDest": f"M{random.randint(1000000000, 9999999999)}",
                # IEEE-CIS specific features
                "TransactionAmt": float(step_plan.amount),
                "ProductCD": product_cd,
                "card1": card1,
                "card2": card2,
                "card4": card4,
                "card6": card6,
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
            logger.info(f"[SyntheticIdentity] Persisted event {event_doc['event_id']} to MongoDB.")
        except Exception as mongo_err:
            logger.error(f"Failed to persist event: {mongo_err}")
            
        return event_doc
