# policy_hash: 5299ddb1a20179b3acd6dafeb84ea5a0a3bedb668c9152aee47bf63de703dc31
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 11335.82
# best_prompt_performance: 11335.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004824.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 368.216673679626  # OPT_PARAM: {"initial": 368.216673679626, "min": 300, "max": 700, "type": "float"}
    safety_stock = 98.42256170416975  # OPT_PARAM: {"initial": 98.42256170416975, "min": 80, "max": 300, "type": "float"}
    demand_forecast_factor = 0.9646991198141729  # OPT_PARAM: {"initial": 0.9646991198141729, "min": 0.8, "max": 2.0, "type": "float"}
    smoothing_factor = 0.08028110317546501  # OPT_PARAM: {"initial": 0.08028110317546501, "min": 0.0, "max": 0.2, "type": "float"}
    lead_time = 4  # OPT_PARAM: {"initial": 4, "min": 3, "max": 6, "type": "int"}
    pipeline_weight_factor = 0.9692458126886022  # OPT_PARAM: {"initial": 0.9692458126886022, "min": 0.3, "max": 1.0, "type": "float"}
    min_order_threshold = 19.991405325579333  # OPT_PARAM: {"initial": 19.991405325579333, "min": 10, "max": 100, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate future demand using weighted average of pipeline orders
    if pipeline_orders:
        # Exponential weights with more emphasis on recent orders
        n = len(pipeline_orders)
        weights = [pipeline_weight_factor ** (n - i - 1) for i in range(n)]
        weights = [w / sum(weights) for w in weights]
        avg_recent_demand = sum(w * d for w, d in zip(weights, pipeline_orders))
    else:
        avg_recent_demand = 0

    # Forecast lead time demand with adjusted factor
    forecast_demand = avg_recent_demand * demand_forecast_factor * lead_time

    # Dynamic order-up-to level based on both base stock and safety stock
    order_up_to = max(base_stock, safety_stock + forecast_demand)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply minimal smoothing only if significant change
    if pipeline_orders and len(pipeline_orders) >= 2 and abs(raw_order - pipeline_orders[-1]) > min_order_threshold:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_orders[-1]
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
