# policy_hash: 78b65089f93ad5a89d00f16de836bc7b091d69841dd875d0a187206bb0453f66
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 704.24
# best_prompt_performance: 704.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225658.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 290.02947461216064  # OPT_PARAM: {"initial": 290.02947461216064, "min": 290, "max": 330, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 35, "max": 50, "type": "float"}
    demand_forecast = 95.69084142157499  # OPT_PARAM: {"initial": 95.69084142157499, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.12, "type": "float"}
    lead_time_factor = 1.25  # OPT_PARAM: {"initial": 1.25, "min": 1.1, "max": 1.4, "type": "float"}
    threshold_factor = 0.7209354020679124  # OPT_PARAM: {"initial": 0.7209354020679124, "min": 0.7, "max": 0.9, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.8, "max": 1.0, "type": "float"}
    min_order = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 10.0, "max": 25.0, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight ** i for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust safety stock based on lead time
    adjusted_safety = safety_stock * lead_time_factor

    # Calculate order-up-to level
    order_up_to = max(base_stock, demand_forecast + adjusted_safety)

    # Calculate raw order amount
    raw_order = max(0, order_up_to - inventory_position)

    # Apply threshold-based smoothing with minimum order constraint
    if raw_order > demand_forecast * threshold_factor:
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = raw_order

    # Ensure minimum order size
    final_order = max(smoothed_order, min_order)

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
