# policy_hash: e7e545e9f89f2cd9b47e936161df6b10a07f2f15936b9ea02354817bd24f3c00
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 34
# source_prompt_files: 1
# best_target_performance: 1168.65
# best_prompt_performance: 1168.65
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_091738.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 258.9018724827205  # OPT_PARAM: {"initial": 258.9018724827205, "min": 200, "max": 350, "type": "float"}
    safety_stock = 23.901872482716  # OPT_PARAM: {"initial": 23.901872482716, "min": 10, "max": 80, "type": "float"}
    demand_estimate_factor = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.7, "max": 1.2, "type": "float"}
    order_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using recent pipeline arrivals
    # For L=2, use weighted average of last two arrivals
    if len(pipeline_orders) >= 2:
        # Use weighted average with more weight on most recent
        if pipeline_orders[0] > 0 or pipeline_orders[1] > 0:
            # Weighted average: 0.7 for most recent, 0.3 for previous
            estimated_demand = (pipeline_orders[0] * 0.7 + pipeline_orders[1] * 0.3) * demand_estimate_factor
        else:
            estimated_demand = 100.0  # default when no recent data
    else:
        estimated_demand = 100.0

    # Calculate order-up-to level
    # Base stock adjusted by safety stock
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - net_inventory)

    # Apply smoothing: blend raw order with estimated demand
    # This prevents overreacting to inventory fluctuations
    smoothed_order = raw_order * order_smoothing + estimated_demand * (1 - order_smoothing)

    # Ensure order is non-negative
    order_amount = max(0, smoothed_order)

    # Round to nearest integer
    return order_amount
