import os
import sys
import asyncio
import uuid
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("run_campaign")

# Add backend folder to python search path
BACKEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend")
sys.path.append(BACKEND_DIR)

# Load env variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

from app.agents.card_tester import CardTesterAgent
from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database

async def main():
    print("[+] Beginning Card Tester Campaign Generation & Simulation...")
    
    # 1. Initialize MongoDB connection
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"[-] MongoDB initialization failed: {e}")
        print("[-] Make sure your MONGODB_URI is set correctly in .env.")
        sys.exit(1)
        
    db = get_database()
    
    # 2. Instantiate Card Tester Agent
    print("[+] Instantiating Card Tester Agent...")
    agent = CardTesterAgent()
    
    # 3. Plan the Campaign
    print("[+] Asking Gemini (Flash) to plan the campaign steps...")
    objective = "Test active card status and validation of a stolen card number with a target balance of $500."
    target_profile = "Standard consumer debit/credit card, active status, no prior alert logs."
    
    try:
        plan = agent.plan(objective, target_profile)
        print("\n" + "=" * 60)
        print(f"CAMPAIGN OBJECTIVE: {plan.objective}")
        print("=" * 60)
        for step in plan.steps:
            print(f"Step {step.step_number}: {step.transaction_type} of ${step.amount:.2f}")
            print(f"  Merchant Category: {step.merchant_category}")
            print(f"  Timing Spacing: {step.spacing_seconds} seconds")
            print(f"  Rationale: {step.rationale}")
            print("-" * 60)
    except Exception as plan_err:
        print(f"[-] Campaign planning failed: {plan_err}")
        await close_mongo_connection()
        sys.exit(1)
        
    # 4. Execute and Project via Synthesizer
    print("\n[+] Simulating and projecting campaign steps through PaySim generator...")
    round_id = f"test-round-{uuid.uuid4().hex[:6]}"
    generated_events = []
    
    for step in plan.steps:
        try:
            event = await agent.act(step, round_id=round_id)
            generated_events.append(event)
            print(f"  [Acted] Step {step.step_number}: Emitted event {event['event_id']}")
            print(f"    Amount: ${event['amount']:.2f} | Type: {event['payload']['type']}")
            print(f"    Account Orig: {event['payload']['nameOrig']} (Bal: ${event['payload']['oldbalanceOrg']:.2f} -> ${event['payload']['newbalanceOrig']:.2f})")
            print(f"    Account Dest: {event['payload']['nameDest']} (Bal: ${event['payload']['oldbalanceDest']:.2f} -> ${event['payload']['newbalanceDest']:.2f})")
            print("-" * 50)
        except Exception as act_err:
            print(f"[-] Failed executing step {step.step_number}: {act_err}")
            
    # 5. Verify database records
    print("\n[+] Verifying records saved in MongoDB events collection...")
    try:
        db_count = await db.events.count_documents({"round_id": round_id})
        print(f"  - Successfully verified: {db_count} events written to MongoDB events collection.")
        
        # Spot-check one document
        if db_count > 0:
            doc = await db.events.find_one({"round_id": round_id})
            print("\n[+] Spot-checking MongoDB Event Document Shape:")
            print("{" )
            print(f"  'event_id': '{doc['event_id']}',")
            print(f"  'round_id': '{doc['round_id']}',")
            print(f"  'persona': '{doc['persona']}',")
            print(f"  'amount': {doc['amount']},")
            print(f"  'is_synthetic_attack': {doc['is_synthetic_attack']},")
            print(f"  'payload': {list(doc['payload'].keys())}")
            print("}")
    except Exception as db_err:
        print(f"[-] MongoDB verification check failed: {db_err}")
        
    # 6. Shutdown database connection
    await close_mongo_connection()
    print("\n[+] Campaign simulation run completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
