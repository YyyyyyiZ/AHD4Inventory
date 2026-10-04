# policy_hash: 7db7236bc91b6c26d153c6921dc28c637eec7e0a031d46be88d154aef0f70e24
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 31
# source_prompt_files: 1
# best_target_performance: 1223.3
# best_prompt_performance: 1223.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_233801.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 330.711228237562  # OPT_PARAM: {"initial": 330.711228237562, "min": 250, "max": 350, "type": "float"}
    safety_stock = 52.57807579221604  # OPT_PARAM: {"initial": 52.57807579221604, "min": 20, "max": 60, "type": "float"}
    pipeline_weight = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    demand_buffer = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.9, "max": 1.2, "type": "float"}
    pipeline_cap = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.2, "max": 0.6, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective base stock
    effective_base = base_stock * demand_buffer

    # Calculate weighted pipeline for lead time demand estimation
    if len(pipeline_orders) > 0:
        weighted_pipeline = 0
        total_weight = 0
        for i, order in enumerate(pipeline_orders):
            # Exponential weighting: newer orders get higher weight
            weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
            weighted_pipeline += order * weight
            total_weight += weight

        avg_weighted_pipeline = weighted_pipeline / total_weight if total_weight > 0 else 0

        # More conservative pipeline adjustment with cap
        pipeline_adjustment = min(pipeline_cap * base_stock,
                                 max(0, avg_weighted_pipeline - base_stock * 0.3))
        target_inventory = effective_base + safety_stock - pipeline_adjustment
    else:
        target_inventory = effective_base + safety_stock

    # Calculate order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply adjustment factor with rounding
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
