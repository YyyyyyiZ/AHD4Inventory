# policy_hash: 3adf243a530686ed57adc17643db438d3e9f8d7a9e8dd63d60997a2b3154ca90
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 1480.16
# best_prompt_performance: 1480.16
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004224.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 404.166365354718  # OPT_PARAM: {"initial": 404.166365354718, "min": 350, "max": 500, "type": "float"}
    safety_stock = 17.109927157082474  # OPT_PARAM: {"initial": 17.109927157082474, "min": 10, "max": 80, "type": "float"}
    demand_forecast = 91.7627978785047  # OPT_PARAM: {"initial": 91.7627978785047, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    pipeline_weight = 0.510482183021008  # OPT_PARAM: {"initial": 0.510482183021008, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on pipeline composition
    pipeline_avg = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    dynamic_adjustment = max(0, (demand_forecast - pipeline_avg) * 0.5)
    order_up_to = base_stock + safety_stock + dynamic_adjustment

    # Calculate order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure order is integer and non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
