from app.agents.base import BaseAgent
from app.agents.card_tester import CardTesterAgent
from app.agents.synthetic_identity import SyntheticIdentityAgent
from app.agents.structuring import StructuringAgent
from app.agents.phishing import PhishingAgent
from app.agents.fake_invoice import FakeInvoiceAgent

def get_agent(persona_name: str) -> BaseAgent:
    """Agent Factory to resolve Red Team persona agents dynamically."""
    name = persona_name.lower().replace("-", "_").strip()
    
    if name == "card_tester":
        return CardTesterAgent()
    elif name == "synthetic_identity":
        return SyntheticIdentityAgent()
    elif name == "structuring" or name == "smurfing":
        return StructuringAgent()
    elif name == "phishing" or name == "bec":
        return PhishingAgent()
    elif name == "fake_invoice":
        return FakeInvoiceAgent()
    else:
        raise ValueError(f"Unknown agent persona name: '{persona_name}'")
