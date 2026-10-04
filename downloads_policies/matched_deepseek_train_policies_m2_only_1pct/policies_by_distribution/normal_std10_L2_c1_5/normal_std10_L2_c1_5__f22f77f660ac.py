# policy_hash: f22f77f660acc76697653e1a855f647594f47be56002e9199c5dff89288f4395
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 39
# source_prompt_files: 1
# best_target_performance: 1200.74
# best_prompt_performance: 1200.74
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_235611.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 297.3879744084716  # OPT_PARAM: {"initial": 297.3879744084716, "min": 200, "max": 500, "type": "float"}
    safety_stock = 9.092170714461702  # OPT_PARAM: {"initial": 9.092170714461702, "min": 0, "max": 50, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    weighted_pipeline = pipeline_weight * sum(pipeline_orders)
    effective_inventory = on_hand_inventory + weighted_pipeline

    # Calculate order amount with safety stock
    order_amount = max(0, base_stock - effective_inventory + safety_stock)

    # Apply smoothing based on recent orders
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if pipeline_orders and len(pipeline_orders) > 0:
        recent_order = pipeline_orders[-1]
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * recent_order
        order_amount = max(0, smoothed_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
