import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.orchestrator.runner import CampaignOrchestrator
from app.agents.card_tester import CardTesterAgent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

class RunRoundRequest(BaseModel):
    objective: Optional[str] = Field(
        default="Validate active credit/debit card status with small-value checks up to a target balance of $500.",
        description="The fraud campaign objective."
    )
    target_profile: Optional[str] = Field(
        default="Standard consumer card, active status, no prior velocity alerts.",
        description="The customer card profile details to simulate against."
    )

@router.post("/run")
async def trigger_campaign_round(request: Optional[RunRoundRequest] = None):
    """
    Triggers a closed-loop simulation round using the Card Tester agent.
    Generates a campaign, projects events, scores via detector, and persists metrics.
    """
    if request is None:
        request = RunRoundRequest()

    logger.info("[Orchestrator API] Received trigger request for new round...")
    try:
        # Instantiate agent and orchestrator
        agent = CardTesterAgent()
        orchestrator = CampaignOrchestrator()

        # Run the round
        round_summary, executed_events = await orchestrator.run_round(
            agent=agent,
            objective=request.objective,
            target_profile=request.target_profile
        )

        return {
            "status": "success",
            "round_summary": round_summary,
            "events_count": len(executed_events),
            "events": [
                {
                    "event_id": ev["event_id"],
                    "step_number": ev["payload"]["step_number"],
                    "type": ev["payload"]["type"],
                    "amount": ev["amount"],
                    "merchant_category": ev["merchant_category"],
                    "detection": ev["detection_result"]
                }
                for ev in executed_events
            ]
        }

    except Exception as e:
        logger.error(f"[Orchestrator API] Failed running round simulation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Campaign execution failed: {str(e)}"
        )
