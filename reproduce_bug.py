
import sys
from pathlib import Path

# Add src to python path
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.intake import IntakeAgent

def reproduction():
    agent = IntakeAgent()
    user_input = "500$ 3 dnya"
    
    print(f"Testing input: '{user_input}'")
    
    try:
        # We expect this to default to _mock_parse because it's short
        result, question = agent.parse(user_input)
        
        if result:
            print(f"Result Budget: {result.budget_usd}")
            print(f"Result Duration: {result.duration_days}")
            print(f"Result: {result}")
        else:
            print(f"Question: {question}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    reproduction()
