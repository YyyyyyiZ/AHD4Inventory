# policy_hash: 2f273bf320c5a07ec3cb03416fd0bcb758d58fe961a6193759795a158b394b4b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 900.22
# best_prompt_performance: 900.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075757.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 419.6586646330836  # OPT_PARAM: {"initial": 419.6586646330836, "min": 380, "max": 480, "type": "float"}
    safety_stock = 24.65866463308365  # OPT_PARAM: {"initial": 24.65866463308365, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 99.69215520290494  # OPT_PARAM: {"initial": 99.69215520290494, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.25, "type": "float"}
    pipeline_weight = 0.3773143168892722  # OPT_PARAM: {"initial": 0.3773143168892722, "min": 0.2, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted sum with decay)
    effective_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        effective_pipeline += order * (pipeline_weight ** (i + 1))

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock - effective_pipeline

    # Calculate order quantity
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
