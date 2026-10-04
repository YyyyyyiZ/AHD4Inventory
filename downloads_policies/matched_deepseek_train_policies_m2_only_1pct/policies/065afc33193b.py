# policy_hash: 065afc33193bd450c5b518545c333ab2050701649e77292f35e22ebe35ed7bd8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 12520.78
# best_prompt_performance: 12520.5
# best_rel_error_pct: 0.002236
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_101304.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.2149111172795  # OPT_PARAM: {"initial": 380.2149111172795, "min": 200, "max": 500, "type": "float"}
    safety_stock = 179.19028706995272  # OPT_PARAM: {"initial": 179.19028706995272, "min": 100, "max": 300, "type": "float"}
    pipeline_coverage = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_forecast_window = 10  # OPT_PARAM: {"initial": 10, "min": 5, "max": 20, "type": "int"}
    forecast_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 0.8, "type": "float"}
    lost_sales_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}
    min_order_threshold = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 50, "type": "float"}
    max_order_cap = 500.0  # OPT_PARAM: {"initial": 500.0, "min": 300, "max": 800, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast from recent pipeline arrivals
    recent_arrivals = pipeline_orders[:min(demand_forecast_window, len(pipeline_orders))]
    avg_recent = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand
    adjusted_base = base_stock * (1 - forecast_weight) + avg_recent * forecast_weight

    # Apply lost-sales penalty to safety stock
    adjusted_safety = safety_stock * lost_sales_multiplier

    # Calculate order-up-to level
    order_up_to = adjusted_base + adjusted_safety

    # Calculate order amount with pipeline consideration
    order_amount = max(0, order_up_to - pipeline_coverage * inventory_position)

    # Apply practical constraints
    if order_amount < min_order_threshold:
        order_amount = 0
    order_amount = min(order_amount, max_order_cap)

    return order_amount
