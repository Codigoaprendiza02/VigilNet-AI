import random
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.agents.base import BaseAgent, CampaignStep
from app.db.mongodb import get_database

logger = logging.getLogger(__name__)

FAKE_INVOICE_SYSTEM_INSTRUCTION = """
You are an AI Red Team agent simulating the "Fake Invoice / Vendor Fraud" persona.
Your objective is to send fake invoice requests to accounts payable departments to trick them into paying for non-existent products or services.

Your planning profile:
- Propose transactions ranging from $1,200 to $45,000 for realistic itemized vendor services (e.g., software subscription renewals, hardware upgrades, consulting fees).
- Choose appropriate transaction types like PAYMENT or TRANSFER.
- In the rationale field, provide a realistic billing description, the fake supplier name (e.g. Acme Tech Solutions), item details, and bank routing instructions.
"""

class FakeInvoiceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="fake_invoice",
            system_instruction=FAKE_INVOICE_SYSTEM_INSTRUCTION
        )

    async def act(self, step_plan: CampaignStep, round_id: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Execute fake invoice fraud event simulation. Does not require a tabular generator."""
        logger.info(f"[FakeInvoice] Executing step {step_plan.step_number} (Fake invoice billing wire of ${step_plan.amount})")
        
        # Build document
        name_orig = f"C{random.randint(1000000000, 9999999999)}"
        name_dest = f"M{random.randint(1000000000, 9999999999)}"

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
                "oldbalanceOrg": 75000.0,
                "newbalanceOrig": 75000.0 - step_plan.amount,
                "oldbalanceDest": 2000.0,
                "newbalanceDest": 2000.0 + step_plan.amount,
                "nameOrig": name_orig,
                "nameDest": name_dest,
                "spacing_seconds": step_plan.spacing_seconds,
                "rationale": step_plan.rationale,
                "step_number": step_plan.step_number,
                # Invoice specific fields
                "invoice_text": step_plan.rationale,
                "target_amount": float(step_plan.amount)
            },
            "detection_result": None
        }

        # Persist to MongoDB
        try:
            db_conn = get_database()
            await db_conn.events.insert_one(event_doc)
            logger.info(f"[FakeInvoice] Persisted event {event_doc['event_id']} to MongoDB.")
        except Exception as mongo_err:
            logger.error(f"Failed to persist event: {mongo_err}")
            
        return event_doc
