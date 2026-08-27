import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_ensemble")

# Add backend folder to python search path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "backend"))

# Load env variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.detectors.ensemble import EnsembleScorer

# Prepare mock events representing different persona types
mock_events = [
    {
        "name": "Card Tester Attack",
        "persona": "card_tester",
        "amount": 1.50,
        "merchant_category": "online_gaming",
        "payload": {
            "type": "PAYMENT",
            "oldbalanceOrg": 5000.0,
            "newbalanceOrig": 4998.50,
            "oldbalanceDest": 1000.0,
            "newbalanceDest": 1001.50,
            "nameOrig": "C1234567890",
            "nameDest": "M9876543210",
            "spacing_seconds": 10
        }
    },
    {
        "name": "Structuring Attack (Smurfing)",
        "persona": "structuring",
        "amount": 8900.00,
        "merchant_category": "unknown",
        "payload": {
            "type": "TRANSFER",
            "oldbalanceOrg": 50000.0,
            "newbalanceOrig": 41100.0,
            "oldbalanceDest": 2000.0,
            "newbalanceDest": 10900.0,
            "nameOrig": "C_SMURF_SENDER",
            "nameDest": "C_MULE_ACCT",
            "spacing_seconds": 120
        }
    },
    {
        "name": "BEC Phishing Attack (Spear-Phishing)",
        "persona": "phishing",
        "amount": 45000.00,
        "merchant_category": "consulting",
        "payload": {
            "type": "TRANSFER",
            "phishing_text": (
                "Hi David, We need you to urgently wire $45,000 for the acquisition retainer "
                "to our offshore legal counsel. Use routing number 98218274. Confirm once sent."
            ),
            "nameOrig": "C_CEO",
            "nameDest": "C_SCAMMER",
            "spacing_seconds": 120
        }
    },
    {
        "name": "Vendor Invoice Spoofing",
        "persona": "fake_invoice",
        "amount": 14200.00,
        "merchant_category": "software_licenses",
        "payload": {
            "type": "PAYMENT",
            "invoice_text": (
                "Invoice IN-98281 for AWS Cloud Server Licensing renewals. "
                "Due immediately: $14,200. Standard payment routing command updated. "
                "Remit to Acme Cloud Inc."
            ),
            "nameOrig": "C_AP_DEPT",
            "nameDest": "M_FAKE_SUPPLIER",
            "spacing_seconds": 300
        }
    },
    {
        "name": "Legitimate Account Transfer (Control)",
        "persona": "legitimate",
        "amount": 250.00,
        "merchant_category": "grocery",
        "payload": {
            "type": "PAYMENT",
            "oldbalanceOrg": 1000.0,
            "newbalanceOrig": 750.0,
            "oldbalanceDest": 12000.0,
            "newbalanceDest": 12250.0,
            "nameOrig": "C_NORMAL_USER",
            "nameDest": "M_GROCERY_STORE",
            "spacing_seconds": 86400
        }
    }
]

async def main():
    print("[+] Starting Ensemble Scorer Verification Run...")
    await connect_to_mongo()
    
    scorer = EnsembleScorer()
    
    results = []
    
    print("\n" + "=" * 80)
    print("SCORING TEST TRANSACTIONS THROUGH METALLIC ENSEMBLE:")
    print("=" * 80)
    
    for event in mock_events:
        print(f"\nEvaluating: {event['name']} ({event['persona'].upper()})")
        res = await scorer.score_transaction(event)
        
        results.append({
            "name": event["name"],
            "meta_score": res["fraud_probability"],
            "flagged": res["is_flagged"],
            "tabular": res["layers"]["tabular"],
            "graph": res["layers"]["graph"],
            "sequence": res["layers"]["sequence"],
            "text": res["layers"]["text"]
        })
        
    print("\n" + "=" * 100)
    print("DETECTOR ENSEMBLE SCORE CONTRIBUTION MATRIX:")
    print("=" * 100)
    print(f"{'Transaction Pattern':<32} | {'Tabular':<7} | {'Graph':<7} | {'Sequence':<8} | {'Text':<7} | {'Meta-Score':<10} | {'Outcome'}")
    print("-" * 100)
    
    for r in results:
        outcome = "FLAGGED (FR)" if r["flagged"] else "CLEAN"
        print(
            f"{r['name']:<32} | "
            f"{r['tabular']*100:>6.1f}% | "
            f"{r['graph']*100:>6.1f}% | "
            f"{r['sequence']*100:>7.1f}% | "
            f"{r['text']*100:>6.1f}% | "
            f"{r['meta_score']*100:>9.1f}% | "
            f"{outcome}"
        )
    print("=" * 100)
    
    await close_mongo_connection()
    print("\n[+] Ensemble verification run complete!")

if __name__ == "__main__":
    asyncio.run(main())
