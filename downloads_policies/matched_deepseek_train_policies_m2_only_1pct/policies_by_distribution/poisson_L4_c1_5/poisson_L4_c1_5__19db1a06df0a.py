# policy_hash: 19db1a06df0ac46e0f804dac5983453cf5299368b596a84db32cc9a925334bfe
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 32
# source_prompt_files: 1
# best_target_performance: 1241.83
# best_prompt_performance: 1242.64
# best_rel_error_pct: 0.065226
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_191642.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 414.7061418587427  # OPT_PARAM: {"initial": 414.7061418587427, "min": 350, "max": 550, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 20, "max": 60, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}
    order_threshold = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock

    # Use the maximum of base_stock and target_position
    order_up_to = max(base_stock, target_position)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing only if order amount is significant
    if order_amount > order_threshold * demand_forecast:
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer for practical ordering
    return order_amount
