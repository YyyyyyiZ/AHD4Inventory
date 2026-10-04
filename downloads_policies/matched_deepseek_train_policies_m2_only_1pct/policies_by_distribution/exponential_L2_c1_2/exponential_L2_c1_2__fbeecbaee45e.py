# policy_hash: fbeecbaee45e0248650c47a7c6a16cd9f8a692d9adb1e029fc6b1828fc47d6b6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 6289.26
# best_prompt_performance: 6288.76
# best_rel_error_pct: 0.007950
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_103923.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 185.69647393014642  # OPT_PARAM: {"initial": 185.69647393014642, "min": 100, "max": 500, "type": "float"}
    safety_stock = 23.278475041178275  # OPT_PARAM: {"initial": 23.278475041178275, "min": 20, "max": 200, "type": "float"}
    demand_buffer = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    if len(pipeline_orders) > 1:
        recent_arrivals = (pipeline_orders[0] + pipeline_orders[1]) / 2

    # Adjust target based on demand pattern
    adjusted_target = base_stock + safety_stock
    if recent_arrivals > base_stock * 0.8:
        adjusted_target *= demand_buffer

    # Calculate order amount
    order_amount = max(0, adjusted_target - inventory_position)

    # Round to nearest integer
    return order_amount
