import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_multi_persona")

# Add backend folder to python search path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "backend"))

# Load env variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.agents import get_agent
from app.orchestrator.runner import CampaignOrchestrator

async def main():
    print("[+] Starting Multi-Persona Expansion Verification Run...")
    
    # 1. Initialize MongoDB connection
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"[-] MongoDB initialization failed: {e}")
        sys.exit(1)
        
    db = get_database()
    
    # Define our 5 personas
    personas = [
        "card_tester",
        "synthetic_identity",
        "structuring",
        "phishing",
        "fake_invoice"
    ]
    
    challenge_results = []
    
    # 2. Iterate and run one round for each persona
    for persona in personas:
        print("\n" + "=" * 60)
        print(f"RUNNING ROUND FOR PERSONA: {persona.upper()}")
        print("=" * 60)
        
        try:
            agent = get_agent(persona)
            orchestrator = CampaignOrchestrator()
            
            objective = f"Trigger mock attack campaign simulating {persona}."
            target_profile = f"Target profile suited for {persona} execution."
            
            round_summary, executed_events = await orchestrator.run_round(
                agent=agent,
                objective=objective,
                target_profile=target_profile
            )
            
            print(f"\n[+] round completed for {persona}!")
            print(f"    Round ID:      {round_summary['round_id']}")
            print(f"    Evasion Rate:  {round_summary['evasion_rate'] * 100:.2f}%")
            print(f"    Blocked Steps: {round_summary['blocked_steps']}/{round_summary['total_steps']}")
            
            challenge_results.append({
                "persona": persona,
                "round_id": round_summary['round_id'],
                "total_steps": round_summary['total_steps'],
                "blocked_steps": round_summary['blocked_steps'],
                "evasion_rate": round_summary['evasion_rate']
            })
            
        except Exception as e:
            print(f"[-] Persona {persona} round failed: {e}")
            challenge_results.append({
                "persona": persona,
                "round_id": "ERROR",
                "total_steps": 0,
                "blocked_steps": 0,
                "evasion_rate": 0.0
            })
            
    # 3. Print final report
    print("\n" + "=" * 60)
    print("FINAL MULTI-PERSONA EXPANSION REPORT:")
    print("=" * 60)
    print(f"{'Persona Name':<20} | {'Round ID':<15} | {'Evasion Rate':<15} | {'Outcome'}")
    print("-" * 60)
    for res in challenge_results:
        print(f"{res['persona']:<20} | {res['round_id']:<15} | {res['evasion_rate']*100:>11.2f}% | {res['blocked_steps']}/{res['total_steps']} steps blocked")
    print("=" * 60)
    
    # 4. Shutdown connection
    await close_mongo_connection()
    print("\n[+] Verification run complete!")

if __name__ == "__main__":
    asyncio.run(main())
