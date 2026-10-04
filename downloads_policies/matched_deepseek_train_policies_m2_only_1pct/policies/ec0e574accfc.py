# policy_hash: ec0e574accfcd7baf7bd1485f673c3b457cdc7b45bb3de5e4b5dc2e8e8b5e16f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 30
# source_prompt_files: 1
# best_target_performance: 10182.15
# best_prompt_performance: 10182.15
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232708.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 342.4954436490819  # OPT_PARAM: {"initial": 342.4954436490819, "min": 100, "max": 800, "type": "float"}
    safety_stock = 72.59544364907981  # OPT_PARAM: {"initial": 72.59544364907981, "min": 20, "max": 200, "type": "float"}
    smoothing_factor = 0.4209911394289906  # OPT_PARAM: {"initial": 0.4209911394289906, "min": 0.3, "max": 1.0, "type": "float"}
    demand_anticipation_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using recent pipeline orders as proxy
    # (older pipeline orders reflect past demand patterns)
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Last two orders placed
        estimated_demand = sum(recent_orders) / len(recent_orders)
    else:
        estimated_demand = 0

    # Dynamic target considering upcoming demand
    dynamic_target = base_stock + safety_stock + demand_anticipation_factor * estimated_demand

    # Calculate order needed to reach dynamic target
    order_needed = max(0, dynamic_target - inventory_position)

    # Apply smoothing with higher factor for more responsiveness
    if order_needed > 0:
        order_amount = smoothing_factor * order_needed
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
