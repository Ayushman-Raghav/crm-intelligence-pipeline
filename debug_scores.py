from src.agents.da_agent import run_da_agent
from src.agents.csm_agent import rule_based_score

reports = run_da_agent()
for r in reports:
    tier, red, green = rule_based_score(r)
    print(f"{tier:5} red={red} green={green}  {r['account_name']}")