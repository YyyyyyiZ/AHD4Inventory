# policy_hash: eab978cd24015e6bbebbd9a6e5d40f5da4f6cea4e6d0be3ecc57d57e4f1da7e9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 45
# source_prompt_files: 1
# best_target_performance: 791.04
# best_prompt_performance: 791.4
# best_rel_error_pct: 0.045510
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_053804.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 499.2607213827695  # OPT_PARAM: {"initial": 499.2607213827695, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 162.39825501779123  # OPT_PARAM: {"initial": 162.39825501779123, "min": 0, "max": 200, "type": "float"}
    adjustment_factor = 0.20008564556026026  # OPT_PARAM: {"initial": 0.20008564556026026, "min": 0.1, "max": 1.5, "type": "float"}
    demand_forecast_factor = 1.3166789145498428  # OPT_PARAM: {"initial": 1.3166789145498428, "min": 0.5, "max": 1.5, "type": "float"}
    pipeline_weight = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.0, "max": 0.8, "type": "float"}

    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline composition
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    adjusted_base = base_stock * (1 + 0.1 * (weighted_pipeline / (base_stock + 1e-6) - 1))

    # Incorporate demand forecast adjustment
    target_level = adjusted_base + safety_stock * demand_forecast_factor

    # Smooth adjustment with non-linear response
    gap = target_level - inventory_position
    if gap > 0:
        order_amount = max(0, gap * adjustment_factor)
    else:
        # More aggressive reduction when overstocked
        order_amount = max(0, gap * adjustment_factor * 1.2)

    # Round to nearest integer for practical ordering
    return order_amount
