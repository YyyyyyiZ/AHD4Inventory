# policy_hash: d160af35bf755842b5cae64e397e0e09997b491042714b4c12c3c75235bb087a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 795.08
# best_prompt_performance: 794.97
# best_rel_error_pct: 0.013835
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_234403.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 355.67761435148077  # OPT_PARAM: {"initial": 355.67761435148077, "min": 300, "max": 600, "type": "float"}
    safety_stock = 56.60649728204722  # OPT_PARAM: {"initial": 56.60649728204722, "min": 50, "max": 150, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lead_time_demand_buffer = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 3.0, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}
    min_order_threshold = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate lead time demand using weighted average of pipeline orders
    if len(pipeline_orders) > 0:
        # Give more weight to recent orders
        weights = [pipeline_weight ** i for i in range(len(pipeline_orders))]
        weights = [w / sum(weights) for w in weights]
        weighted_avg = sum(p * w for p, w in zip(pipeline_orders, weights))
        lead_time_demand_estimate = weighted_avg * lead_time_demand_buffer
    else:
        lead_time_demand_estimate = 0

    # Calculate target inventory position
    target_position = base_stock + safety_stock + lead_time_demand_estimate

    # Calculate order quantity
    order_needed = max(0, target_position - inventory_position)

    # Apply adjustment factor
    order_amount = adjustment_factor * order_needed

    # Apply minimum order threshold
    if order_amount < min_order_threshold:
        order_amount = 0

    # Round to nearest integer
    return order_amount
