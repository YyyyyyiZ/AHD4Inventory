# policy_hash: adf6c3aac9899baa3db1bf79bf326425a27270866156e4b4ab6bc40a6bca156d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 8159.5
# best_prompt_performance: 8159.5
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_002808.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 502.9988103123368  # OPT_PARAM: {"initial": 502.9988103123368, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 0, "max": 300, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_variance = sum((q - demand_forecast) ** 2 for q in pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_risk_factor = 1.0 + min(0.5, pipeline_variance / 10000.0)  # OPT_PARAM: {"initial": 10000.0, "min": 1000, "max": 50000, "type": "float"}

    # Dynamic base stock adjustment
    dynamic_base_stock = base_stock * pipeline_risk_factor

    # Calculate order-up-to level with safety stock
    order_up_to = dynamic_base_stock + safety_stock

    # Smooth ordering to avoid large fluctuations
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer (maintain non-negative)
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
