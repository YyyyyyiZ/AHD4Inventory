# policy_hash: f3558e9bf83b78b0b3f77aaa45bc1530ff248f864abc4e31601075d0112cf60b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 10307.66
# best_prompt_performance: 10307.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232323.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.1141943749648  # OPT_PARAM: {"initial": 380.1141943749648, "min": 200, "max": 500, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 10, "max": 80, "type": "float"}
    demand_estimate = 130.0  # OPT_PARAM: {"initial": 130.0, "min": 80, "max": 200, "type": "float"}
    pipeline_factor = 0.7983281977589065  # OPT_PARAM: {"initial": 0.7983281977589065, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing = 0.29888546517260434  # OPT_PARAM: {"initial": 0.29888546517260434, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline coverage
    if len(pipeline_orders) > 0:
        pipeline_coverage = sum(pipeline_orders) * pipeline_factor
    else:
        pipeline_coverage = 0

    # Adjust base stock based on pipeline coverage
    adjusted_base = base_stock - pipeline_coverage

    # Calculate order-up-to level
    order_up_to = max(adjusted_base, demand_estimate + safety_stock)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    if raw_order > 0 and len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        smoothed_order = smoothing * raw_order + (1 - smoothing) * avg_pipeline
        order_amount = max(0, smoothed_order)
    else:
        order_amount = raw_order

    return order_amount
