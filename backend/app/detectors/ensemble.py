import os
import logging
import pandas as pd
import xgboost as xgb
from typing import Dict, Any, Optional

from app.detectors.features import extract_features, FEATURE_COLS
from app.detectors.graph import GraphDetector
from app.detectors.sequence import SequenceDetector
from app.detectors.text_detector import TextDetector

logger = logging.getLogger(__name__)

class TabularDetector:
    def __init__(self):
        self.model = None

    def get_model(self) -> xgb.XGBClassifier:
        if self.model is None:
            # Resolve root directory: backend/app/detectors/ensemble.py -> 4 levels up
            root_dir = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            model_path = os.path.join(root_dir, "models", "detector.json")

            if not os.path.exists(model_path):
                raise FileNotFoundError(
                    f"Tabular detector model not found at {model_path}. "
                    "Please run train_detector.py first."
                )

            self.model = xgb.XGBClassifier()
            self.model.load_model(model_path)
            logger.info("Ensemble Tabular model loaded successfully.")

        return self.model

    def score_event(self, event: Dict[str, Any]) -> float:
        try:
            features = extract_features(event)
            df = pd.DataFrame([features])[FEATURE_COLS]
            model = self.get_model()
            prob = float(model.predict_proba(df)[0][1])
            return prob
        except Exception as e:
            logger.warning(f"Tabular scoring failed: {e}. Defaulting to 0.0")
            return 0.0

class EnsembleScorer:
    def __init__(self):
        self.tabular = TabularDetector()
        self.graph = GraphDetector()
        self.sequence = SequenceDetector()
        self.text = TextDetector()

    async def score_transaction(self, event: Dict[str, Any], round_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs transaction scoring across all 4 defense layers
        and combines them using the meta soft-OR combination rule.
        """
        # Execute each layer
        tab_score = self.tabular.score_event(event)
        graph_score = await self.graph.score_event(event, round_id=round_id)
        seq_score = await self.sequence.score_event(event, round_id=round_id)
        text_score = await self.text.score_event(event)

        # Meta Ensemble Soft-OR Maximum Logic
        meta_score = max(tab_score, graph_score, seq_score, text_score)

        return {
            "fraud_probability": float(meta_score),
            "is_flagged": meta_score >= 0.5,
            "layers": {
                "tabular": float(tab_score),
                "graph": float(graph_score),
                "sequence": float(seq_score),
                "text": float(text_score)
            }
        }
