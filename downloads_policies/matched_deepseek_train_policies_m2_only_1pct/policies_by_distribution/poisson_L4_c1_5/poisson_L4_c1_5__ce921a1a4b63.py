# policy_hash: ce921a1a4b633a5771ea85af23bf787abb0dd66a4e42545f9ce16937dc00c98b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1698.9
# best_prompt_performance: 1698.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003157.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 459.8593770614001  # OPT_PARAM: {"initial": 459.8593770614001, "min": 300, "max": 600, "type": "float"}
    safety_stock = 62.324202057814496  # OPT_PARAM: {"initial": 62.324202057814496, "min": 0, "max": 150, "type": "float"}
    demand_forecast = 110.28845789596284  # OPT_PARAM: {"initial": 110.28845789596284, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.2549468615221384  # OPT_PARAM: {"initial": 0.2549468615221384, "min": 0.1, "max": 0.9, "type": "float"}
    pipeline_weight = 0.8616962769261238  # OPT_PARAM: {"initial": 0.8616962769261238, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted average)
    if pipeline_orders:
        weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(reversed(pipeline_orders)))
        pipeline_factor = weighted_pipeline / (sum(pipeline_orders) + 1e-6)
    else:
        pipeline_factor = 1.0

    # Dynamic base stock adjustment based on pipeline status
    dynamic_base_stock = base_stock * pipeline_factor

    # Calculate order-up-to level
    order_up_to = dynamic_base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
