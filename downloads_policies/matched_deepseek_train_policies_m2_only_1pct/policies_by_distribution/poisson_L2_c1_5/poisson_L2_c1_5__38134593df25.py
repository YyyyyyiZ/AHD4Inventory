# policy_hash: 38134593df25202e987bb83bf5a502ec8de240d1600f0da77fb93e71ac73d589
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1351.8
# best_prompt_performance: 1351.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070610.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 288.90855799684635  # OPT_PARAM: {"initial": 288.90855799684635, "min": 250, "max": 350, "type": "float"}
    safety_stock = 43.90855799684616  # OPT_PARAM: {"initial": 43.90855799684616, "min": 10, "max": 80, "type": "float"}
    adjustment_factor = 0.7120224917319029  # OPT_PARAM: {"initial": 0.7120224917319029, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    demand_buffer = 13.908557996846254  # OPT_PARAM: {"initial": 13.908557996846254, "min": 0, "max": 30, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline to account for upcoming arrivals
    weighted_pipeline = pipeline_weight * pipeline_orders[0] if pipeline_orders else 0

    # Calculate target inventory level with dynamic adjustment
    target_inventory = base_stock + safety_stock + demand_buffer - weighted_pipeline

    # Calculate order amount with smoothing
    raw_order = max(0, target_inventory - inventory_position)
    adjusted_order = raw_order * adjustment_factor

    # Add small rounding buffer to prevent under-ordering
    if adjusted_order > 0 and adjusted_order < 1:
        adjusted_order = 1.0

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
