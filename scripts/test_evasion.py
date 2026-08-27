import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("test_evasion")

# Add backend folder to python search path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(ROOT_DIR, "backend"))

# Load env variables
load_dotenv(os.path.join(ROOT_DIR, ".env"))

from app.db.mongodb import connect_to_mongo, close_mongo_connection, get_database
from app.agents.card_tester import CardTesterAgent
from app.orchestrator.runner import CampaignOrchestrator

async def main():
    print("[+] Starting 3-Round Evasion & Adaptation Simulation Loop...")
    
    # 1. Initialize MongoDB connection
    try:
        await connect_to_mongo()
    except Exception as e:
        print(f"[-] MongoDB initialization failed: {e}")
        sys.exit(1)
        
    # 2. Instantiate Agent and Orchestrator
    agent = CardTesterAgent()
    orchestrator = CampaignOrchestrator()
    
    objective = "Test card validator sequence up to $500 target balance."
    target_profile = "Standard consumer debit card, active status, no prior logs."
    
    rounds_history = []
    num_rounds = 3
    
    for r in range(1, num_rounds + 1):
        print("\n" + "=" * 60)
        print(f"ROUND {r} OF {num_rounds} CHALLENGE START")
        print("=" * 60)
        
        try:
            # Run the round
            round_summary, executed_events = await orchestrator.run_round(
                agent=agent,
                objective=objective,
                target_profile=target_profile
            )
            
            rounds_history.append(round_summary)
            
            print(f"\n[+] Round {r} Completed!")
            print(f"    Round ID:      {round_summary['round_id']}")
            print(f"    Evasion Rate:  {round_summary['evasion_rate'] * 100:.2f}%")
            print(f"    Blocked Steps: {round_summary['blocked_steps']}/{round_summary['total_steps']}")
            
            # Pass feedback back for adaptation if not the final round
            if r < num_rounds:
                brief = orchestrator.generate_evasion_brief(round_summary, executed_events)
                print("\n[+] GENERATED EVASION FEEDBACK BRIEF SENT TO GEMINI:")
                print("-" * 50)
                print(brief)
                print("-" * 50)
                
                agent.adapt(brief)
                print(f"[+] Feedbacks recorded in Red Team agent memory. Adapting for Round {r+1}...")
                
        except Exception as e:
            print(f"[-] Round {r} failed: {e}")
            break
            
    # 3. Print Final Progression Chart
    print("\n" + "=" * 60)
    print("FINAL CHALLENGE EVASION PROGRESSION:")
    print("=" * 60)
    print(f"{'Round #':<10} | {'Round ID':<15} | {'Evasion Rate':<15} | {'Outcome'}")
    print("-" * 60)
    for idx, r_summary in enumerate(rounds_history, 1):
        print(f"Round {idx:<5} | {r_summary['round_id']:<15} | {r_summary['evasion_rate']*100:>11.2f}% | {r_summary['blocked_steps']} steps blocked")
    print("=" * 60)
    
    # 4. Shutdown database connection
    await close_mongo_connection()
    print("\n[+] Evasion verification script completed!")

if __name__ == "__main__":
    asyncio.run(main())
