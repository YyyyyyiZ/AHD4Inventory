# policy_hash: 5113e6aa032a6d4210447338f811625c5e9fcdb80c0592102192771533341590
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1200.1
# best_prompt_performance: 1199.64
# best_rel_error_pct: 0.038330
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_040156.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 306.34080994016296  # OPT_PARAM: {"initial": 306.34080994016296, "min": 150, "max": 400, "type": "float"}
    demand_buffer = 15.1  # OPT_PARAM: {"initial": 15.1, "min": 5, "max": 40, "type": "float"}
    pipeline_weight = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    smoothing = 0.3225996134175083  # OPT_PARAM: {"initial": 0.3225996134175083, "min": 0.1, "max": 0.6, "type": "float"}

    # Inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from recent pipeline activity
    if len(pipeline_orders) >= 2:
        recent_activity = sum(pipeline_orders[-2:]) / 2.0
        demand_estimate = recent_activity + demand_buffer
    else:
        demand_estimate = base_stock * 0.3

    # Adjust target based on pipeline status
    pipeline_adjustment = pipeline_weight * (sum(pipeline_orders) - len(pipeline_orders) * demand_estimate)
    target = base_stock + pipeline_adjustment

    # Calculate order
    needed = max(0, target - inventory_position)

    # Smooth with previous order if available
    if pipeline_orders:
        previous_order = pipeline_orders[-1]
        order = smoothing * needed + (1 - smoothing) * previous_order
    else:
        order = needed

    # Ensure non-negative integer
    order_amount = max(0, int(round(order)))

    return order_amount
