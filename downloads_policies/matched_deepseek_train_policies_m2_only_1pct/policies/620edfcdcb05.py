# policy_hash: 620edfcdcb05d5655c579e30566caf96476c1ed900bbb7e993d6aa677757abfa
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1043.5
# best_prompt_performance: 1043.5
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_061338.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 290.96409000018724  # OPT_PARAM: {"initial": 290.96409000018724, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 11.964088686264772  # OPT_PARAM: {"initial": 11.964088686264772, "min": 0, "max": 100, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Adjust base stock based on pipeline composition
    # Give more weight to near-term arrivals
    weighted_pipeline = 0
    for i, q in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)  # Higher weight for earlier arrivals
        weighted_pipeline += q * weight

    # Calculate target inventory position
    target_position = base_stock + safety_stock - weighted_pipeline * 0.1

    # Calculate order amount
    order_amount = max(0, target_position - net_inventory)

    # Round to integer (since order amount must be int)
    return order_amount
