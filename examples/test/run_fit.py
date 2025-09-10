import collections
import requests
import json
import re
import textwrap


def clean_json_string(s):
    # Remove triple backticks and optional language tag
    s = re.sub(r"^```[a-zA-Z]*\n?", "", s.strip())
    s = re.sub(r"```$", "", s.strip())
    return s.strip()
# -------------------- Evaluation Function --------------------
def calculate_exact_cost(policy, demand_real, lead_time, holding_cost, lost_sale_cost, initial_inventory=0):
    if lead_time < 0:
        raise ValueError("Lead time must be non-negative.")
    
    T = len(demand_real)
    outstanding = collections.deque([0] * lead_time)
    on_hand = initial_inventory
    total_holding = 0.0
    total_lost = 0.0
    
    ending_inventories = []
    shortages = []
    
    for t in range(T):
        arrival = outstanding.popleft() if lead_time > 0 else 0
        on_hand += arrival
        
        pipeline = sum(outstanding)
        
        Q = policy(on_hand, pipeline)
        # print(Q)
        if Q < 0:
            raise ValueError("Policy returned negative order quantity.")
        
        if lead_time == 0:
            on_hand += Q
        else:
            outstanding.append(Q)
        
        D = demand_real[t]
        if on_hand >= D:
            on_hand -= D
            lost = 0
        else:
            lost = D - on_hand
            on_hand = 0
        
        total_holding += holding_cost * on_hand
        total_lost += lost_sale_cost * lost
        
        ending_inventories.append(on_hand)
        shortages.append(lost)
    
    return total_holding + total_lost, ending_inventories, shortages

def generate_better_heuristic(current_description, current_policy_code, demand_realization, sim_results_str):
    api_key = "sk-5d290dc8a98e43c99f0e5d09ffb40d72"  # Replace with your key
    url = "https://api.deepseek.com/chat/completions"
    
    system_prompt = "You are an expert in inventory management and developing heuristics for stochastic demand problems."
    
    # JSON-output enforcing prompt
    user_prompt = f"""
You are given an inventory control problem with stochastic demand and a fixed lead time of 1 period, which means that the order you placed at this period will arrive at the next period.
The system starts at period 0 with on-hand inventory = 0 and no pipeline orders.
Orders placed at the start of period k will arrive at the start of period k+1 before demand is realized.
For each time period, the previous order first come, and then we make a order for this period, and finally the demand comes.
Lost sales cost = 10 per unit of unmet demand in a period.
Holding cost = 2 per unit of positive ending inventory in a period.
The total cost is the sum over all periods: holding cost applies to positive ending inventory, shortage cost applies to the absolute value of negative ending inventory.

My current policy is:
{current_description}

The code for the current policy is:
```python
{current_policy_code}
The exact demand realization sequence is:
{demand_realization}
The simulation results for the current policy on this demand realization are:
{sim_results_str}
These results show the exact amount of extra units (ending_inventory > 0) or units not enough (shortage > 0) in each period.
Your task:


Analyze the simulation results and demand realization to identify patterns where the current policy is overstocking (extra units) or understocking (not enough units).


Propose a new ordering policy that minimizes the total cost as much as possible for this specific demand realization, using insights from the extra/not enough units to adjust ordering logic.


The ordering decision at each period may depend only on the current on-hand inventory and pipeline inventory, and must not use any future demand information.


Return your answer as a valid JSON object with exactly three fields:
"description": a one-sentence description of your algorithm,
"code": a complete Python function definition named policy that takes exactly two arguments (current_inventory, pipeline_inventory) and returns a non-negative integer order quantity.
"answer": answer the following question: - What are your motivations of generating a new policy from the old one? Base your reasoning on analyzing the simulation results, including patterns of extra units or units not enough. Please calculate the final cost for the current policy step by step using the simulation results (period_cost = 2 * ending_inventory + 10 * shortage for each period, then total). Then, simulate the new policy step by step, calculate the cost for each period and the total cost to verify your intuition and proposed policy is truly better than the current policy.


Do not include any extra text outside the JSON.
"""
    messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": user_prompt}
    ]
    payload = {
    "model": "deepseek-reasoner",
    "messages": messages,
    "stream": False
    }
    headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")
    
    response_data = response.json()

    raw_output = response_data['choices'][0]['message']['content']
    print(raw_output)
    c = input()
    raw_output = clean_json_string(raw_output)
    try:
        parsed = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output is not valid JSON: {raw_output}") from e
    
    return parsed["description"], parsed["code"]


if __name__ == "__main__":
    demand = [48,50,56,49,51,52,43,51,46,52,44,50,49,49,44,46,43,45,44,51,59,52,51,54,58,53,43,46,47,45,53,58,69,46,49,38,48,48,48,54,49,43,51,48,58,59,62,48,47,49]
    # demand = [20, 20, 20, 20]
    current_policy_code = textwrap.dedent("""
    def policy(current_inventory, pipeline_inventory):
        base_stock = 160
        inventory_position = current_inventory + pipeline_inventory
        return max(0, base_stock - inventory_position)
    """)
    current_description = "A base-stock policy with base-stock level 160."
    M = 10
    costs = []
    for i in range(M):
        exec(current_policy_code, globals())
        cost, ending_inventories, shortages = calculate_exact_cost(policy, demand, lead_time=1, holding_cost=2.0, lost_sale_cost=10.0, initial_inventory=0)
        costs.append(cost)
        print(f"Iteration {i}: inventory = {ending_inventories}, shortage = {shortages}, cost = {cost}")
        sim_results_str = "\n".join(
        [f"Period {t}: demand={demand[t]}, ending_inventory={ending_inventories[t]}, shortage={shortages[t]}"
        for t in range(len(demand))]
        )
        description, new_code = generate_better_heuristic(current_description, current_policy_code, str(demand), sim_results_str)
        print(f"Iteration {i} description: {description}")
        print(f"Iteration {i} code: {new_code}")
        current_description = description
        current_policy_code = new_code  # Replace policy code for next round
    print("Costs over iterations:", costs)