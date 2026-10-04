# policy_hash: ab82e6c0244005abbacf523c348963a48e0a2063427d92fda0d193853efa0574
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 7148.52
# best_prompt_performance: 7148.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091452.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 354.49279964445407  # OPT_PARAM: {"initial": 354.49279964445407, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.5561260272657568  # OPT_PARAM: {"initial": 0.5561260272657568, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand pattern
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base_stock, safety_stock)

    # Place order to reach order-up-to level
    order_amount = max(0, order_up_to - inventory_position)

    return order_amount
