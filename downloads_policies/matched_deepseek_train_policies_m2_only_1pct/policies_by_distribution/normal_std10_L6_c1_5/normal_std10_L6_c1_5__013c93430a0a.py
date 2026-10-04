# policy_hash: 013c93430a0ae52a9e0fb9f5a6af78f28d4670018548ba3ca37fdf42680c5b4f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 1248.57
# best_prompt_performance: 1248.57
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_012613.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 820.0  # OPT_PARAM: {"initial": 820.0, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 80.9338605263506  # OPT_PARAM: {"initial": 80.9338605263506, "min": 50, "max": 150, "type": "float"}
    demand_forecast = 97.0572407797563  # OPT_PARAM: {"initial": 97.0572407797563, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.012064399377158511  # OPT_PARAM: {"initial": 0.012064399377158511, "min": 0.0, "max": 0.2, "type": "float"}
    lead_time_multiplier = 1.125332949867882  # OPT_PARAM: {"initial": 1.125332949867882, "min": 1.0, "max": 1.5, "type": "float"}
    pipeline_weight = 0.9277447910782491  # OPT_PARAM: {"initial": 0.9277447910782491, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight ** i for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand over lead time
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_forecast * lead_time * lead_time_multiplier

    # Calculate order-up-to level
    order_up_to = lead_time_demand + safety_stock

    # Use the minimum of base_stock and calculated order-up-to (more conservative)
    final_order_up_to = min(base_stock, order_up_to)

    # Calculate order amount
    order_amount = max(0, final_order_up_to - inventory_position)

    # Apply smoothing with minimum order threshold
    if order_amount > demand_forecast * 0.5 and smoothing_factor > 0:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    return order_amount
