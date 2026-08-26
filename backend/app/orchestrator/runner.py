import uuid
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from app.db.mongodb import get_database
from app.detectors.features import extract_features, FEATURE_COLS
from app.routers.score import detector_manager
from app.agents.base import BaseAgent

logger = logging.getLogger(__name__)

class CampaignOrchestrator:
    def __init__(self):
        pass

    async def run_round(
        self, 
        agent: BaseAgent, 
        objective: str, 
        target_profile: str
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Orchestrates a single campaign round:
        1. Asks the Red Team agent to plan.
        2. Executes each step, feeding output through the statistical generator.
        3. Routes each transaction through the Blue Team detector.
        4. Updates events with detection feedback.
        5. Saves the overall round summary in MongoDB.
        """
        round_id = f"round-{uuid.uuid4().hex[:6]}"
        logger.info(f"[Orchestrator] Initiating round {round_id} for persona: {agent.name}")

        # 1. Generate plan using Gemini
        plan = agent.plan(objective, target_profile)
        logger.info(f"[Orchestrator] Successfully generated plan with {len(plan.steps)} steps.")

        total_steps = len(plan.steps)
        blocked_steps = 0
        executed_events = []
        db = get_database()

        # 2. Iterate through steps
        for step in plan.steps:
            logger.info(f"[Orchestrator] Executing Step {step.step_number}...")
            
            # Agent generates the event (projects through PaySim generator and writes to MongoDB)
            event = await agent.act(step, round_id=round_id)
            
            # Score transaction using XGBoost
            prob_fraud = 0.0
            is_flagged = False
            action = "allowed"
            
            try:
                features = extract_features(event)
                df = pd.DataFrame([features])[FEATURE_COLS]
                
                model = detector_manager.get_model()
                prob_fraud = float(model.predict_proba(df)[0][1])
                is_flagged = prob_fraud >= 0.5
                action = "blocked" if is_flagged else "allowed"
                
                logger.info(f"[Orchestrator] Step {step.step_number} score: {prob_fraud:.4f} -> Action: {action.upper()}")
            except FileNotFoundError as fnf:
                logger.warning(
                    f"[Orchestrator] Tabular model not found. "
                    "Allowing transaction by default. Please run scripts/train_detector.py."
                )
                action = "allowed (no detector)"
            except Exception as e:
                logger.error(f"[Orchestrator] Error scoring transaction at Step {step.step_number}: {e}")
                action = "allowed (error)"

            if is_flagged:
                blocked_steps += 1

            # 3. Construct detection result and update database event doc
            detection_result = {
                "fraud_probability": prob_fraud,
                "is_flagged": is_flagged,
                "action": action,
                "scored_at": datetime.utcnow()
            }
            
            event["detection_result"] = detection_result
            executed_events.append(event)

            # Update event in MongoDB with detection outcome
            try:
                await db.events.update_one(
                    {"event_id": event["event_id"]},
                    {"$set": {"detection_result": detection_result}}
                )
            except Exception as mongo_err:
                logger.error(f"Failed to update detection result in MongoDB: {mongo_err}")

        # 4. Compute metrics & save Round Summary
        evasion_rate = (total_steps - blocked_steps) / total_steps if total_steps > 0 else 1.0
        
        round_doc = {
            "round_id": round_id,
            "persona": agent.name,
            "status": "completed",
            "total_steps": total_steps,
            "blocked_steps": blocked_steps,
            "evasion_rate": evasion_rate,
            "timestamp": datetime.utcnow()
        }

        try:
            await db.rounds.insert_one(round_doc)
            logger.info(f"[Orchestrator] Successfully persisted round {round_id} to MongoDB.")
        except Exception as mongo_err:
            logger.error(f"Failed to save round document: {mongo_err}")

        round_doc.pop("_id", None)
        return round_doc, executed_events
