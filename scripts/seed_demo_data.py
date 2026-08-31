import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("seed_demo_data")

# Add backend folder to python search path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "backend"))

# Load env variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database

# Pre-defined progression profiles showing round-over-round evasion decay (defense improvement)
seed_profiles = {
    "card_tester": {
        "objective": "Validate active credit/debit card status with small-value checks.",
        "rounds": [
            # Round 1: High evasion (detector tabular/sequence missed)
            {
                "evasion_rate": 1.0,
                "total_steps": 3,
                "blocked_steps": 0,
                "events": [
                    {"amount": 1.50, "type": "PAYMENT", "mcc": "online_gaming", "scores": {"tabular": 0.05, "graph": 0.08, "sequence": 0.12, "text": 0.0}, "flagged": False},
                    {"amount": 2.20, "type": "PAYMENT", "mcc": "online_gaming", "scores": {"tabular": 0.08, "graph": 0.08, "sequence": 0.15, "text": 0.0}, "flagged": False},
                    {"amount": 1.90, "type": "PAYMENT", "mcc": "online_gaming", "scores": {"tabular": 0.06, "graph": 0.08, "sequence": 0.22, "text": 0.0}, "flagged": False}
                ]
            },
            # Round 2: Moderate evasion (sequence layer triggers slightly)
            {
                "evasion_rate": 0.66,
                "total_steps": 3,
                "blocked_steps": 1,
                "events": [
                    {"amount": 3.10, "type": "PAYMENT", "mcc": "subscription", "scores": {"tabular": 0.15, "graph": 0.08, "sequence": 0.35, "text": 0.0}, "flagged": False},
                    {"amount": 2.80, "type": "PAYMENT", "mcc": "subscription", "scores": {"tabular": 0.22, "graph": 0.08, "sequence": 0.48, "text": 0.0}, "flagged": False},
                    {"amount": 4.50, "type": "PAYMENT", "mcc": "subscription", "scores": {"tabular": 0.25, "graph": 0.08, "sequence": 0.62, "text": 0.0}, "flagged": True} # Blocked by velocity sequence
                ]
            },
            # Round 3: Low evasion (sequence/tabular lock-on)
            {
                "evasion_rate": 0.0,
                "total_steps": 3,
                "blocked_steps": 3,
                "events": [
                    {"amount": 5.20, "type": "PAYMENT", "mcc": "rideshare", "scores": {"tabular": 0.48, "graph": 0.08, "sequence": 0.58, "text": 0.0}, "flagged": True},
                    {"amount": 4.90, "type": "PAYMENT", "mcc": "rideshare", "scores": {"tabular": 0.52, "graph": 0.08, "sequence": 0.68, "text": 0.0}, "flagged": True},
                    {"amount": 6.10, "type": "PAYMENT", "mcc": "rideshare", "scores": {"tabular": 0.56, "graph": 0.08, "sequence": 0.72, "text": 0.0}, "flagged": True}
                ]
            }
        ]
    },
    "structuring": {
        "objective": "Evade CTR flags by splitting transaction flows.",
        "rounds": [
            # Round 1: High evasion
            {
                "evasion_rate": 1.0,
                "total_steps": 3,
                "blocked_steps": 0,
                "events": [
                    {"amount": 8500.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.12, "graph": 0.15, "sequence": 0.08, "text": 0.0}, "flagged": False},
                    {"amount": 9200.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.15, "graph": 0.18, "sequence": 0.08, "text": 0.0}, "flagged": False},
                    {"amount": 8900.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.14, "graph": 0.22, "sequence": 0.08, "text": 0.0}, "flagged": False}
                ]
            },
            # Round 2: Moderate evasion (GCN graph propagation triggers)
            {
                "evasion_rate": 0.33,
                "total_steps": 3,
                "blocked_steps": 2,
                "events": [
                    {"amount": 7100.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.18, "graph": 0.45, "sequence": 0.08, "text": 0.0}, "flagged": False},
                    {"amount": 6800.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.22, "graph": 0.65, "sequence": 0.08, "text": 0.0}, "flagged": True}, # Graph link flagged
                    {"amount": 7500.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.25, "graph": 0.78, "sequence": 0.08, "text": 0.0}, "flagged": True} # Graph link flagged
                ]
            },
            # Round 3: Perfect recall (GCN maps mule network fully)
            {
                "evasion_rate": 0.0,
                "total_steps": 3,
                "blocked_steps": 3,
                "events": [
                    {"amount": 5400.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.28, "graph": 0.85, "sequence": 0.08, "text": 0.0}, "flagged": True},
                    {"amount": 5200.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.32, "graph": 0.89, "sequence": 0.08, "text": 0.0}, "flagged": True},
                    {"amount": 5900.00, "type": "TRANSFER", "mcc": "unknown", "scores": {"tabular": 0.30, "graph": 0.92, "sequence": 0.08, "text": 0.0}, "flagged": True}
                ]
            }
        ]
    },
    "phishing": {
        "objective": "Conduct BEC spear-phishing wire transfers.",
        "rounds": [
            # Round 1: High evasion (phishing text missed)
            {
                "evasion_rate": 1.0,
                "total_steps": 2,
                "blocked_steps": 0,
                "events": [
                    {"amount": 42000.00, "type": "TRANSFER", "mcc": "consulting", "scores": {"tabular": 0.12, "graph": 0.15, "sequence": 0.08, "text": 0.10}, "flagged": False, "text": "Hi Bob, can you process invoice IN-9828 immediately?"},
                    {"amount": 38000.00, "type": "TRANSFER", "mcc": "consulting", "scores": {"tabular": 0.15, "graph": 0.15, "sequence": 0.08, "text": 0.15}, "flagged": False, "text": "Update requested for Acme consulting payments."}
                ]
            },
            # Round 2: Partial evasion (Urgency text patterns recognized)
            {
                "evasion_rate": 0.5,
                "total_steps": 2,
                "blocked_steps": 1,
                "events": [
                    {"amount": 29000.00, "type": "TRANSFER", "mcc": "consulting", "scores": {"tabular": 0.15, "graph": 0.15, "sequence": 0.08, "text": 0.38}, "flagged": False, "text": "Please check the attached contract update from Acme."},
                    {"amount": 31000.00, "type": "TRANSFER", "mcc": "consulting", "scores": {"tabular": 0.18, "graph": 0.15, "sequence": 0.08, "text": 0.92}, "flagged": True, "text": "URGENT: Process routing update for the Acme acquisition retainer wire immediately."} # Text model locks on
                ]
            },
            # Round 3: Zero evasion (Prompted text layer flags both variants)
            {
                "evasion_rate": 0.0,
                "total_steps": 2,
                "blocked_steps": 2,
                "events": [
                    {"amount": 22000.00, "type": "TRANSFER", "mcc": "consulting", "scores": {"tabular": 0.18, "graph": 0.15, "sequence": 0.08, "text": 0.94}, "flagged": True, "text": "URGENT: Verify update routing path for supplier retainer wire."},
                    {"amount": 24000.00, "type": "TRANSFER", "mcc": "consulting", "scores": {"tabular": 0.20, "graph": 0.15, "sequence": 0.08, "text": 0.95}, "flagged": True, "text": "Acme payment update instructions attached. Dispatch immediately."}
                ]
            }
        ]
    },
    "fake_invoice": {
        "objective": "Inject fake supplier renewal billing invoices.",
        "rounds": [
            # Round 1: High evasion
            {
                "evasion_rate": 1.0,
                "total_steps": 2,
                "blocked_steps": 0,
                "events": [
                    {"amount": 12500.00, "type": "PAYMENT", "mcc": "software_licenses", "scores": {"tabular": 0.05, "graph": 0.08, "sequence": 0.08, "text": 0.18}, "flagged": False, "text": "Standard software billing license renewal Acme Corp."},
                    {"amount": 14200.00, "type": "PAYMENT", "mcc": "software_licenses", "scores": {"tabular": 0.08, "graph": 0.08, "sequence": 0.08, "text": 0.22}, "flagged": False, "text": "AWS cloud server hosting fees IN-98281."}
                ]
            },
            # Round 2: Partial evasion
            {
                "evasion_rate": 0.5,
                "total_steps": 2,
                "blocked_steps": 1,
                "events": [
                    {"amount": 9500.00, "type": "PAYMENT", "mcc": "software_licenses", "scores": {"tabular": 0.08, "graph": 0.08, "sequence": 0.08, "text": 0.35}, "flagged": False, "text": "Vite React template licensing invoice."},
                    {"amount": 11800.00, "type": "PAYMENT", "mcc": "software_licenses", "scores": {"tabular": 0.08, "graph": 0.08, "sequence": 0.08, "text": 0.96}, "flagged": True, "text": "URGENT: Cloud license renewal fees updated routing command. Due immediately."}
                ]
            },
            # Round 3: Zero evasion
            {
                "evasion_rate": 0.0,
                "total_steps": 2,
                "blocked_steps": 2,
                "events": [
                    {"amount": 8200.00, "type": "PAYMENT", "mcc": "software_licenses", "scores": {"tabular": 0.12, "graph": 0.08, "sequence": 0.08, "text": 0.95}, "flagged": True, "text": "License fees update invoice. Routing details updated. Due immediately."},
                    {"amount": 8700.00, "type": "PAYMENT", "mcc": "software_licenses", "scores": {"tabular": 0.14, "graph": 0.08, "sequence": 0.08, "text": 0.96}, "flagged": True, "text": "AWS server renewal billing invoice. Remit updated account path."}
                ]
            }
        ]
    },
    "synthetic_identity": {
        "objective": "Open fraudulent credit lines with synthetic profiles.",
        "rounds": [
            # Round 1: High evasion
            {
                "evasion_rate": 1.0,
                "total_steps": 2,
                "blocked_steps": 0,
                "events": [
                    {"amount": 1500.00, "type": "PAYMENT", "mcc": "electronics", "scores": {"tabular": 0.22, "graph": 0.10, "sequence": 0.08, "text": 0.0}, "flagged": False},
                    {"amount": 1800.00, "type": "PAYMENT", "mcc": "electronics", "scores": {"tabular": 0.28, "graph": 0.10, "sequence": 0.08, "text": 0.0}, "flagged": False}
                ]
            },
            # Round 2: Partial evasion
            {
                "evasion_rate": 0.5,
                "total_steps": 2,
                "blocked_steps": 1,
                "events": [
                    {"amount": 2800.00, "type": "PAYMENT", "mcc": "retail", "scores": {"tabular": 0.35, "graph": 0.10, "sequence": 0.08, "text": 0.0}, "flagged": False},
                    {"amount": 4200.00, "type": "PAYMENT", "mcc": "retail", "scores": {"tabular": 0.65, "graph": 0.10, "sequence": 0.08, "text": 0.0}, "flagged": True} # Tabular model correlation checks out
                ]
            },
            # Round 3: Zero evasion
            {
                "evasion_rate": 0.0,
                "total_steps": 2,
                "blocked_steps": 2,
                "events": [
                    {"amount": 4500.00, "type": "PAYMENT", "mcc": "luxury", "scores": {"tabular": 0.72, "graph": 0.15, "sequence": 0.08, "text": 0.0}, "flagged": True},
                    {"amount": 4900.00, "type": "PAYMENT", "mcc": "luxury", "scores": {"tabular": 0.78, "graph": 0.15, "sequence": 0.08, "text": 0.0}, "flagged": True}
                ]
            }
        ]
    }
}

async def seed_data():
    db = get_database()
    
    # Check if rounds collection already has data
    rounds_count = await db.rounds.count_documents({})
    if rounds_count > 0:
        logger.info(f"MongoDB rounds collection already has {rounds_count} documents. Skipping seeding to prevent overwriting.")
        return
        
    logger.info("[+] Seeding 3 rounds of progression metrics per attack persona in MongoDB Atlas...")
    
    # Timestamps in the past to look realistic
    base_time = datetime.utcnow() - timedelta(days=2)
    
    for persona, profile in seed_profiles.items():
        logger.info(f"Generating progression curve records for: {persona.upper()}")
        
        for idx, round_cfg in enumerate(profile["rounds"]):
            round_num = idx + 1
            round_id = f"seed-{persona[:3]}-r{round_num}-{random.randint(100, 999)}"
            round_time = base_time + timedelta(hours=(round_num * 4) + (random.randint(0, 30) / 10))
            
            # 1. Create and insert round document
            # Generate detailed mock evasion brief summary
            brief = (
                f"Campaign Evasion Feedback for Round {round_id}:\n"
                f"Result summary: Out of {round_cfg['total_steps']} steps, {round_cfg['blocked_steps']} steps were BLOCKED by the detector.\n"
                f"Overall Evasion Rate: {round_cfg['evasion_rate'] * 100:.2f}%\n\n"
                "Below is the transaction-by-transaction breakdown:\n"
            )
            for s_idx, ev_cfg in enumerate(round_cfg["events"]):
                step_num = s_idx + 1
                tx_type = ev_cfg["type"]
                amount = ev_cfg["amount"]
                mcc = ev_cfg["mcc"]
                action = "BLOCKED" if ev_cfg["flagged"] else "ALLOWED"
                score = max(ev_cfg["scores"].values())
                brief += f"- Step {step_num}: {tx_type} of ${amount:.2f} at {mcc} -> DECISION: {action} (Detector Score: {score * 100:.2f}%)\n"
            
            brief += (
                "\nADAPTATION DIRECTIVE FOR THE NEXT ROUND:\n"
                "- Modify your transaction variables (reduce amounts, change categories, adjust spacing) "
                "for steps that were BLOCKED so they mimic normal consumer baseline transactions.\n"
                "- Double down on strategies that successfully evaded detection (ALLOWED steps)."
            )

            round_doc = {
                "round_id": round_id,
                "persona": persona,
                "status": "completed",
                "total_steps": round_cfg["total_steps"],
                "blocked_steps": round_cfg["blocked_steps"],
                "evasion_rate": round_cfg["evasion_rate"],
                "evasion_brief": brief,
                "timestamp": round_time
            }
            await db.rounds.insert_one(round_doc)
            
            # 2. Create and insert events for this round
            for step_idx, ev_cfg in enumerate(round_cfg["events"]):
                step_number = step_idx + 1
                event_id = f"evt-seed-{random.randint(100000, 999999)}"
                
                event_doc = {
                    "event_id": event_id,
                    "round_id": round_id,
                    "persona": persona,
                    "amount": ev_cfg["amount"],
                    "merchant_category": ev_cfg["mcc"],
                    "timestamp": round_time + timedelta(minutes=step_number * 10),
                    "payload": {
                        "step_number": step_number,
                        "type": ev_cfg["type"],
                        "nameOrig": f"C_SEED_SENDER_{random.randint(1000, 9999)}",
                        "nameDest": f"M_SEED_RECV_{random.randint(1000, 9999)}",
                        "phishing_text": ev_cfg.get("text", ""),
                        "invoice_text": ev_cfg.get("text", "")
                    },
                    "detection_result": {
                        "fraud_probability": max(ev_cfg["scores"].values()),
                        "is_flagged": ev_cfg["flagged"],
                        "action": "blocked" if ev_cfg["flagged"] else "allowed",
                        "layers": ev_cfg["scores"],
                        "scored_at": round_time + timedelta(minutes=step_number * 10 + 1)
                    }
                }
                await db.events.insert_one(event_doc)
                
    logger.info("[+] Seeding complete! Database is populated with 15 campaign rounds showing clean evasion decay metrics.")

async def main():
    # Parse arguments
    force_clear = False
    if len(sys.argv) > 1 and sys.argv[1] == "--clear":
        force_clear = True
        
    await connect_to_mongo()
    
    if force_clear:
        # User explicitly asked to clear/seed fresh
        db = get_database()
        logger.warning("[!] --clear passed: Dropping existing rounds and events from database...")
        # Delete only seed or test rounds
        await db.rounds.delete_many({})
        await db.events.delete_many({})
        logger.info("[+] Collections cleared.")
        
    await seed_data()
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
