# policy_hash: 57cefc72a2979bcaa70856728527efe271abceb9ed29d807ddf8733310dba1d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1859.73
# best_prompt_performance: 1859.73
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003706.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 488.0487537383287  # OPT_PARAM: {"initial": 488.0487537383287, "min": 300, "max": 600, "type": "float"}
    safety_stock = 42.460698656361316  # OPT_PARAM: {"initial": 42.460698656361316, "min": 10, "max": 60, "type": "float"}
    demand_adjustment = 0.9990591531957602  # OPT_PARAM: {"initial": 0.9990591531957602, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    pipeline_weight = 0.2134084847264791  # OPT_PARAM: {"initial": 0.2134084847264791, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate expected demand from recent pipeline orders
    if len(pipeline_orders) >= 3:
        # Use more recent orders for better demand estimation
        recent_orders = pipeline_orders[-3:]
        avg_recent_order = sum(recent_orders) / len(recent_orders)
        expected_demand = avg_recent_order * demand_adjustment
    else:
        # Fallback to average historical demand
        expected_demand = 100.0

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_ratio = pipeline_weight * (pipeline_sum / (len(pipeline_orders) * 100))
        adjusted_base = base_stock * (1.0 + pipeline_ratio)
    else:
        adjusted_base = base_stock

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock + expected_demand

    # Calculate order amount with smoothing
    order_gap = target_inventory - inventory_position
    if order_gap > 0:
        order_amount = max(0, smoothing_factor * order_gap)
    else:
        order_amount = 0

    # Round to nearest integer
    return order_amount
