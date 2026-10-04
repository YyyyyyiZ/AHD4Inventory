# policy_hash: 402ebdbfecdd8cf99793fcd47e45b06b744f65feed48f92ee82bb6743ccd3856
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 6860.35
# best_prompt_performance: 6860.33
# best_rel_error_pct: 0.000292
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234924.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 259.50078108966545  # OPT_PARAM: {"initial": 259.50078108966545, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 26.537326006053657  # OPT_PARAM: {"initial": 26.537326006053657, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent arrivals
    # Use average of arriving orders in next 2 periods as demand forecast
    arriving_soon = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    forecast_demand = sum(arriving_soon) / max(len(arriving_soon), 1) * demand_forecast_factor

    # Adjust base stock based on forecast
    adjusted_base_stock = base_stock + safety_stock + forecast_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing to avoid extreme order sizes
    smoothing_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        # Smooth large orders
        max_order_jump = 194.85015086881407  # OPT_PARAM: {"initial": 194.85015086881407, "min": 50, "max": 500, "type": "float"}
        order_amount = min(order_amount, max_order_jump) * smoothing_factor + order_amount * (1 - smoothing_factor)

    return order_amount
