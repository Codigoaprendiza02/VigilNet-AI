import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_orchestrator")

# Add backend folder to python search path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "backend"))

# Load env variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.agents.card_tester import CardTesterAgent
from app.orchestrator.runner import CampaignOrchestrator

async def main():
    print("[+] Starting Closed-Loop Orchestrator Verification Run...")
    
    # 1. Initialize MongoDB connection
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"[-] MongoDB initialization failed: {e}")
        sys.exit(1)
        
    db = get_database()
    
    # 2. Instantiate Agent and Orchestrator
    print("[+] Instantiating Card Tester Agent and Campaign Orchestrator...")
    agent = CardTesterAgent()
    orchestrator = CampaignOrchestrator()
    
    objective = "Test card validator sequence up to $500 target balance."
    target_profile = "Standard consumer debit card, active status, no prior logs."
    
    # 3. Run the Round Simulation
    print("[+] Triggering orchestrator run_round...")
    try:
        round_summary, executed_events = await orchestrator.run_round(
            agent=agent,
            objective=objective,
            target_profile=target_profile
        )
        
        # 4. Print results
        print("\n" + "=" * 60)
        print("SIMULATION ROUND RESULTS SUMMARY:")
        print("=" * 60)
        print(f"Round ID:      {round_summary['round_id']}")
        print(f"Persona:       {round_summary['persona']}")
        print(f"Total Steps:   {round_summary['total_steps']}")
        print(f"Blocked Steps: {round_summary['blocked_steps']}")
        print(f"Evasion Rate:  {round_summary['evasion_rate'] * 100:.2f}%")
        print(f"Status:        {round_summary['status']}")
        print("=" * 60)
        
        print("\nTRANSACTION-BY-TRANSACTION DETECTION LOGS:")
        print("-" * 60)
        for ev in executed_events:
            det = ev.get("detection_result", {})
            print(f"Step {ev['payload']['step_number']}: {ev['payload']['type']} of ${ev['amount']:.2f} at {ev['merchant_category']}")
            print(f"  Event ID:    {ev['event_id']}")
            print(f"  Fraud Score: {det.get('fraud_probability', 0.0) * 100:.2f}%")
            print(f"  Decision:    {str(det.get('action')).upper()}")
            print("-" * 60)
            
        # 5. Database Verification Check
        print("\n[+] Querying rounds and events collections in MongoDB to verify persistence...")
        round_db_doc = await db.rounds.find_one({"round_id": round_summary['round_id']})
        
        if round_db_doc:
            print(f"  [PASS] Successfully retrieved round summary from MongoDB rounds collection.")
        else:
            print(f"  [FAIL] Round summary document not found in MongoDB.")
            
        events_in_db = await db.events.count_documents({"round_id": round_summary['round_id']})
        print(f"  [PASS] Successfully retrieved {events_in_db} transaction events associated with this round.")
        
    except Exception as run_err:
        print(f"[-] Simulation execution failed: {run_err}")
        
    # 6. Shutdown database connection
    await close_mongo_connection()
    print("\n[+] Verification run complete!")

if __name__ == "__main__":
    asyncio.run(main())
