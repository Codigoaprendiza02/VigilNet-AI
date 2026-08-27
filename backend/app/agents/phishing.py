import random
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, CampaignStep
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

PHISHING_SYSTEM_INSTRUCTION = """
You are an AI Red Team agent simulating the "Business Email Compromise (BEC) / Phishing" persona.
Your objective is to draft highly targeted, hyper-personalized spear-phishing emails targeting corporate finance officers to execute fraudulent wire transfers.

Your planning profile:
- Propose high-value wire transfers ($5,000 to $95,000) under the guise of urgent invoice settlements or acquisition fees.
- Set transaction_type as TRANSFER or PAYMENT.
- In the rationale field for each step, write the complete drafted email body of your phishing attempt. It must include highly realistic details (e.g., matching corporate urgency, false invoice attachments, payment routing commands).
"""

class PhishingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="phishing",
            system_instruction=PHISHING_SYSTEM_INSTRUCTION
        )

    async def act(self, step_plan: CampaignStep, round_id: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Execute text-based phishing simulation. Does not require a tabular generator."""
        logger.info(f"[Phishing] Executing step {step_plan.step_number} (BEC phishing target wire of ${step_plan.amount})")
        
        # Build document
        name_orig = f"C{random.randint(1000000000, 9999999999)}"
        name_dest = f"C{random.randint(1000000000, 9999999999)}"

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
                "oldbalanceOrg": 100000.0,
                "newbalanceOrig": 100000.0 - step_plan.amount,
                "oldbalanceDest": 5000.0,
                "newbalanceDest": 5000.0 + step_plan.amount,
                "nameOrig": name_orig,
                "nameDest": name_dest,
                "spacing_seconds": step_plan.spacing_seconds,
                "rationale": step_plan.rationale,
                "step_number": step_plan.step_number,
                # Phishing specific text fields
                "phishing_text": step_plan.rationale,
                "target_amount": float(step_plan.amount)
            },
            "detection_result": None
        }

        # Persist to MongoDB
        try:
            db_conn = get_database()
            await db_conn.events.insert_one(event_doc)
            logger.info(f"[Phishing] Persisted event {event_doc['event_id']} to MongoDB.")
        except Exception as mongo_err:
            logger.error(f"Failed to persist event: {mongo_err}")
            
        return event_doc
