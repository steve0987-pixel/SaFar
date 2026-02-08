"""Quick test for DeterministicTripPlanner."""
import sys
sys.path.insert(0, ".")

from src.agents.planner import DeterministicTripPlanner

p = DeterministicTripPlanner()
plan = p.create_plan(days=2, interests=['history', 'food'], budget=100, pace='medium')

print(f"Days: {len(plan['days'])}")
print(f"POIs: {plan['poi_count']}")
print(f"Meals: {plan['meal_count']}")
print(f"Cost: ${plan['total_cost_usd']}")
print(f"Warnings: {plan['warnings']}")

for day in plan['days']:
    print(f"\n{day['theme']}:")
    for b in day['blocks']:
        print(f"  {b['start']}-{b['end']}: {b['name']} ({b['type']})")
