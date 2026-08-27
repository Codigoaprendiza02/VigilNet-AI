import time
import logging
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger(__name__)

class TextScoreResponse(BaseModel):
    is_fraud: bool = Field(description="True if the text is identified as a fraud attempt (phishing, fake invoice, etc.)")
    confidence: float = Field(description="Confidence score from 0.0 to 1.0")
    rationale: str = Field(description="Brief explanation of the decision")

class TextDetector:
    def __init__(self):
        if settings.GEMINI_API_KEY:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY not set. Text detector will return default scores.")

    async def score_event(self, event: Dict[str, Any]) -> float:
        """
        Extracts any text payload (emails, invoices) from the event document
        and prompts Gemini to detect spear-phishing or invoice spoofing.
        """
        if not self.client:
            return 0.0

        payload = event.get("payload", {})
        
        # Collect text inputs
        text_content = ""
        if "phishing_text" in payload:
            text_content = payload["phishing_text"]
        elif "invoice_text" in payload:
            text_content = payload["invoice_text"]
        elif "rationale" in payload and event.get("persona") in ["phishing", "fake_invoice"]:
            text_content = payload["rationale"]

        if not text_content or len(text_content.strip()) < 10:
            # Not a text-based event
            return 0.0

        prompt = (
            "You are an expert fraud investigator system.\n"
            "Analyze the following text payload extracted from a transaction alert.\n"
            "Determine if this text is a fraudulent Business Email Compromise (BEC) spear-phishing attempt, "
            "or a fake invoice spoofing request sent to accounts payable.\n\n"
            f"TEXT TO EVALUATE:\n\"\"\"\n{text_content}\n\"\"\"\n"
        )

        max_attempts = 4
        base_delay = 15

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"[TextDetector] Evaluating text anomaly via {settings.GEMINI_FLASH_MODEL} (Attempt {attempt}/{max_attempts})")
                response = self.client.models.generate_content(
                    model=settings.GEMINI_FLASH_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=TextScoreResponse,
                        system_instruction=(
                            "Analyze text for social engineering signs, urgent payment requests, false invoice spoofing, "
                            "and routing modification requests. Be highly accurate."
                        ),
                        temperature=0.1
                    )
                )

                parsed_res = response.parsed
                if not parsed_res:
                    parsed_res = TextScoreResponse.model_validate_json(response.text)

                if parsed_res.is_fraud:
                    logger.info(f"[TextDetector] Flagged text as fraud! Confidence: {parsed_res.confidence * 100:.2f}% | Rationale: {parsed_res.rationale}")
                    return float(parsed_res.confidence)
                else:
                    logger.info(f"[TextDetector] Text evaluated as clean. Rationale: {parsed_res.rationale}")
                    return 0.0

            except Exception as e:
                err_str = str(e)
                logger.warning(f"[TextDetector] Attempt {attempt} failed: {err_str}")
                if attempt == max_attempts:
                    logger.error(f"[TextDetector] Failed evaluating text after {max_attempts} attempts: {e}")
                    return 0.0

                is_rate_limit = any(term in err_str.lower() for term in ["429", "resource_exhausted", "quota", "rate limit"])
                delay = base_delay * attempt
                if is_rate_limit:
                    delay += 10
                    logger.info(f"[TextDetector] Rate limit hit. Waiting {delay}s before retry...")
                else:
                    logger.info(f"[TextDetector] Transient error. Waiting {delay}s before retry...")
                time.sleep(delay)

        return 0.0
