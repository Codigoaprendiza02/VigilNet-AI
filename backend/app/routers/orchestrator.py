import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.orchestrator.runner import CampaignOrchestrator
from app.agents import get_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

class RunRoundRequest(BaseModel):
    persona: Optional[str] = Field(
        default="card_tester",
        description="Name of the Red Team persona to simulate (e.g. card_tester, synthetic_identity, structuring, phishing, fake_invoice)."
    )
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
        # Instantiate agent dynamically and orchestrator
        agent = get_agent(request.persona)
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


class ChallengeRequest(BaseModel):
    persona: Optional[str] = Field(
        default="card_tester",
        description="Name of the Red Team persona to simulate (e.g. card_tester, synthetic_identity, structuring, phishing, fake_invoice)."
    )
    num_rounds: Optional[int] = Field(
        default=3,
        description="The number of adaptive progression rounds to simulate."
    )
    objective: Optional[str] = Field(
        default="Validate active credit/debit card status with small-value checks up to a target balance of $500.",
        description="The fraud campaign objective."
    )
    target_profile: Optional[str] = Field(
        default="Standard consumer card, active status, no prior velocity alerts.",
        description="The customer card profile details to simulate against."
    )

@router.post("/challenge")
async def trigger_challenge_loop(request: Optional[ChallengeRequest] = None):
    """
    Runs a multi-round adaptive challenge loop.
    Feedback is fed back to the Red Team agent at the end of each round to evade detection.
    """
    if request is None:
        request = ChallengeRequest()

    logger.info(f"[Orchestrator API] Triggering adaptive challenge loop for {request.num_rounds} rounds...")
    try:
        agent = get_agent(request.persona)
        orchestrator = CampaignOrchestrator()
        
        rounds_history = []
        
        for r in range(1, request.num_rounds + 1):
            logger.info(f"[Orchestrator API] Running challenge round {r}/{request.num_rounds}...")
            
            # Execute round
            round_summary, executed_events = await orchestrator.run_round(
                agent=agent,
                objective=request.objective,
                target_profile=request.target_profile
            )
            
            rounds_history.append({
                "round_num": r,
                "round_id": round_summary["round_id"],
                "total_steps": round_summary["total_steps"],
                "blocked_steps": round_summary["blocked_steps"],
                "evasion_rate": round_summary["evasion_rate"]
            })
            
            # Pass feedback back for adaptation if not the final round
            if r < request.num_rounds:
                brief = orchestrator.generate_evasion_brief(round_summary, executed_events)
                agent.adapt(brief)
                logger.info(f"[Orchestrator API] Evasion Brief adapted into agent memory for Round {r+1}.")

        return {
            "status": "success",
            "challenge_summary": {
                "total_rounds_executed": len(rounds_history),
                "final_evasion_rate": rounds_history[-1]["evasion_rate"] if rounds_history else 0.0,
                "rounds": rounds_history
            }
        }

    except Exception as e:
        logger.error(f"[Orchestrator API] Failed running challenge simulation loop: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Challenge loop execution failed: {str(e)}"
        )

