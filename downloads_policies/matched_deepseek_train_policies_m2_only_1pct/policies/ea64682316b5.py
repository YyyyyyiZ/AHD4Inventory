# policy_hash: ea64682316b5d847371e663ae33ed37929146db764d8e09312f78852ca5dfcf0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 49
# source_prompt_files: 1
# best_target_performance: 7164.1
# best_prompt_performance: 7164.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_085928.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 698.7098938402615  # OPT_PARAM: {"initial": 698.7098938402615, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 160.79999999994956  # OPT_PARAM: {"initial": 160.79999999994956, "min": 0, "max": 400, "type": "float"}
    demand_forecast_window = 5  # OPT_PARAM: {"initial": 5, "min": 1, "max": 10, "type": "int"}
    forecast_alpha = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecasting using exponential smoothing (simulated)
    # Since we don't have actual demand history, we'll use a placeholder
    # In practice, this would use recent demand observations
    forecast_demand = 152.3999999999395  # OPT_PARAM: {"initial": 152.3999999999395, "min": 50, "max": 250, "type": "float"}

    # Adjust base stock based on forecast and safety stock
    adjusted_base_stock = base_stock + safety_stock - forecast_demand * demand_forecast_window * forecast_alpha

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply ordering smoothing to reduce bullwhip effect
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    min_order_quantity = 20.1  # OPT_PARAM: {"initial": 20.1, "min": 0, "max": 100, "type": "float"}

    # Smooth the order quantity
    if raw_order > 0:
        order_amount = max(min_order_quantity, raw_order * smoothing_factor)
    else:
        order_amount = 0

    # Round to nearest integer (as required by output type)
    order_amount = int(round(order_amount))

    return order_amount
