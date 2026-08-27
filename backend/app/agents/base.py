import os
import pickle
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger(__name__)

# Structured schemas for Gemini output planning
class CampaignStep(BaseModel):
    step_number: int = Field(description="Step sequence number (1, 2, 3...)")
    transaction_type: str = Field(description="Transaction type. Must be one of: PAYMENT, TRANSFER, CASH_OUT, CASH_IN, DEBIT")
    amount: float = Field(description="Transaction amount in USD")
    merchant_category: str = Field(description="Category of the merchant (e.g. electronics, retail, grocery, gas_station, online_gaming, unknown)")
    spacing_seconds: int = Field(description="Time delay in seconds before executing this step since the previous step")
    rationale: str = Field(description="Brief natural language rationale for why this step helps bypass detection")

class CampaignPlan(BaseModel):
    objective: str = Field(description="Overall campaign objective")
    steps: List[CampaignStep] = Field(description="Ordered list of campaign steps")


class BaseAgent:
    def __init__(self, name: str, system_instruction: str):
        self.name = name
        self.system_instruction = system_instruction
        self.evasion_briefs: List[str] = []
        
        # Initialize Gemini Client (picks up GEMINI_API_KEY from environment)
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY is not set. Gemini API calls will fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            
        self._synthesizer_cache = None

    def load_synthesizer(self, dataset_key: str = "paysim"):
        """Lazy-loads the trained synthesizer model."""
        if self._synthesizer_cache is None:
            models_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
                "models"
            )
            synthesizer_path = os.path.join(models_dir, "synthesizer.pkl")
            
            if not os.path.exists(synthesizer_path):
                raise FileNotFoundError(
                    f"Synthesizer model file not found at {synthesizer_path}. "
                    "Please run train_generator.py first."
                )
                
            logger.info(f"Loading synthesizers from {synthesizer_path}...")
            with open(synthesizer_path, "rb") as f:
                self._synthesizer_cache = pickle.load(f)
                
        if dataset_key not in self._synthesizer_cache:
            raise KeyError(f"Synthesizer for '{dataset_key}' not found in model artifacts.")
            
        return self._synthesizer_cache[dataset_key]

    def plan(self, objective: str, target_profile: str) -> CampaignPlan:
        """Query Gemini using structured output to plan the campaign."""
        if not self.client:
            raise RuntimeError("Gemini client is not initialized. Check GEMINI_API_KEY.")
            
        prompt = (
            f"Plan a payment fraud campaign.\n"
            f"Objective: {objective}\n"
            f"Target Profile: {target_profile}\n"
        )
        
        if self.evasion_briefs:
            prompt += "\nIncorporated Evasion Directives (from prior detection failures):\n"
            for idx, brief in enumerate(self.evasion_briefs, 1):
                prompt += f"Directive {idx}: {brief}\n"
                
        import time
        max_attempts = 4
        base_delay = 15
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Generating campaign plan using model: {settings.GEMINI_FLASH_MODEL} (Attempt {attempt}/{max_attempts})")
                response = self.client.models.generate_content(
                    model=settings.GEMINI_FLASH_MODEL,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=CampaignPlan,
                        system_instruction=self.system_instruction,
                        temperature=0.7
                    )
                )
                
                # The google-genai library returns the parsed Pydantic object in response.parsed
                plan_data = response.parsed
                if not plan_data:
                    # Fallback if parsed is empty but text exists
                    plan_data = CampaignPlan.model_validate_json(response.text)
                    
                return plan_data
                
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Attempt {attempt} failed: {err_str}")
                if attempt == max_attempts:
                    logger.error(f"Error during Gemini planning call after {max_attempts} attempts: {e}")
                    raise e
                
                # Check for rate limit error (429 / Resource Exhausted)
                is_rate_limit = any(term in err_str.lower() for term in ["429", "resource_exhausted", "quota", "rate limit"])
                delay = base_delay * attempt
                if is_rate_limit:
                    delay += 10  # Add safety margin
                    logger.info(f"Detected Gemini API rate limit/quota error. Retrying in {delay}s...")
                else:
                    logger.info(f"Transient error encountered. Retrying in {delay}s...")
                time.sleep(delay)

    async def act(self, step_plan: CampaignStep, round_id: str, feedback: Optional[str] = None) -> Dict[str, Any]:
        """Abstract act method to be implemented by child classes."""
        raise NotImplementedError("Subclasses must implement the act method.")

    def adapt(self, evasion_brief: Optional[str] = None):
        """Append evasion brief directives to prompt context for the next planning phase."""
        if evasion_brief:
            logger.info(f"Agent {self.name} adapting with evasion brief: {evasion_brief}")
            self.evasion_briefs.append(evasion_brief)
