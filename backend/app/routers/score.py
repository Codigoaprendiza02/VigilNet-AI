import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.detectors.ensemble import EnsembleScorer

logger = logging.getLogger(__name__)
router = APIRouter()
ensemble_scorer = EnsembleScorer()

@router.post("/score")
async def score_transaction(event: Dict[str, Any]):
    """
    Exposes an endpoint to score raw transaction events for fraud probability across all active layers.
    """
    try:
        res = await ensemble_scorer.score_transaction(event)
        return {
            "status": "success",
            "fraud_probability": res["fraud_probability"],
            "is_flagged": res["is_flagged"],
            "layers": res["layers"]
        }

    except FileNotFoundError as fnf_err:
        logger.warning(str(fnf_err))
        raise HTTPException(
            status_code=503, 
            detail="Tabular detector model is not trained/available. Please run scripts/train_detector.py."
        )
    except Exception as e:
        logger.error(f"Error scoring transaction: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring failed: {str(e)}")
