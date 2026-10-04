# policy_hash: ed2c27dbf4f1743099743c204f4b4a94db952d0add350f1594cb556dbf609083
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 12708.27
# best_prompt_performance: 12708.26
# best_rel_error_pct: 0.000079
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_101037.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 431.5129436065301  # OPT_PARAM: {"initial": 431.5129436065301, "min": 300, "max": 700, "type": "float"}
    safety_stock = 143.02667181771326  # OPT_PARAM: {"initial": 143.02667181771326, "min": 100, "max": 250, "type": "float"}
    pipeline_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    demand_forecast_window = 8  # OPT_PARAM: {"initial": 8, "min": 5, "max": 15, "type": "int"}
    forecast_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.2, "max": 0.6, "type": "float"}
    lost_sales_penalty_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast from recent pipeline arrivals (proxy for recent demand)
    recent_arrivals = pipeline_orders[:min(demand_forecast_window, len(pipeline_orders))]
    avg_recent = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand patterns
    adjusted_base = base_stock * (1 - forecast_weight) + avg_recent * forecast_weight

    # Apply lost-sales penalty adjustment to safety stock
    adjusted_safety = safety_stock * lost_sales_penalty_factor

    # Calculate order-up-to level
    order_up_to = adjusted_base + adjusted_safety

    # Calculate order amount with pipeline consideration
    order_amount = max(0, order_up_to - pipeline_weight * inventory_position)

    return order_amount
