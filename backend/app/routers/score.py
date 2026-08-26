import os
import logging
import pandas as pd
import xgboost as xgb
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.detectors.features import extract_features, FEATURE_COLS

logger = logging.getLogger(__name__)
router = APIRouter()

class TabularDetectorManager:
    def __init__(self):
        self.model = None

    def get_model(self) -> xgb.XGBClassifier:
        if self.model is None:
            # Resolve root directory path: backend/app/routers/score.py -> 4 levels up to root
            root_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            model_path = os.path.join(root_dir, "models", "detector.json")

            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"Tabular detector model not found at {model_path}. "
                    "Please run train_detector.py first."
                )

            logger.info(f"Loading tabular detector model from {model_path}...")
            self.model = xgb.XGBClassifier()
            self.model.load_model(model_path)
            logger.info("Tabular detector model loaded successfully.")

        return self.model

detector_manager = TabularDetectorManager()

@router.post("/score")
async def score_transaction(event: Dict[str, Any]):
    """
    Exposes an endpoint to score raw transaction events for fraud probability.
    Excludes identifiers and maps metadata through feature engineering.
    """
    try:
        # 1. Feature Engineering
        features = extract_features(event)
        
        # 2. Match exact column ordering expected by model
        df = pd.DataFrame([features])[FEATURE_COLS]
        
        # 3. Predict probability using trained model
        model = detector_manager.get_model()
        
        # predict_proba returns [[prob_0, prob_1]]
        prob_fraud = float(model.predict_proba(df)[0][1])
        
        # Expose a threshold (standard 0.5 probability)
        is_flagged = prob_fraud >= 0.5

        return {
            "status": "success",
            "fraud_probability": prob_fraud,
            "is_flagged": is_flagged
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
