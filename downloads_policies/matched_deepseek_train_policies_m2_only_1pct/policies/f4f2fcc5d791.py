# policy_hash: f4f2fcc5d7919e8c439d65571ee7d6402ca7105a19e1beab7103740da32eeca8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1287.06
# best_prompt_performance: 1287.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_061421.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.0000013139217  # OPT_PARAM: {"initial": 294.0000013139217, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Use average of recent pipeline orders as demand proxy
    if len(pipeline_orders) >= 2:
        recent_demand_estimate = (pipeline_orders[0] + pipeline_orders[1]) / 2 * demand_adjustment
    else:
        recent_demand_estimate = 0

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock + safety_stock + recent_demand_estimate

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - net_inventory)

    # Round to nearest integer (since demand is integer)
    order_amount = int(round(order_amount))

    return order_amount
