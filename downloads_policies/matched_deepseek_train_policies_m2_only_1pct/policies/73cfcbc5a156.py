# policy_hash: 73cfcbc5a156803bec6e09d2cf725ebfa00bf8b2167c7979464803c05a59e3b9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 13
# source_prompt_files: 2
# best_target_performance: 12072.9
# best_prompt_performance: 12072.88
# best_rel_error_pct: 0.000166
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_043326.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 447.61873565622994  # OPT_PARAM: {"initial": 447.61873565622994, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 48.57413232738414  # OPT_PARAM: {"initial": 48.57413232738414, "min": 0, "max": 300, "type": "float"}
    demand_estimate = 110.50865368123169  # OPT_PARAM: {"initial": 110.50865368123169, "min": 10, "max": 500, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Calculate order amount with smoothing
    order_needed = max(0, target_position - inventory_position)

    # Adjust order based on expected demand
    if order_needed > 0:
        # Order at least expected demand, but not more than needed
        order_amount = max(demand_estimate, order_needed)
    else:
        order_amount = 0

    return order_amount
