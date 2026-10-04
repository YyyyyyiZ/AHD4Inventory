# policy_hash: fe2902f882b5a2ea9f6aacc4a62b73192c51edd17c7317182a7d9de607170cfc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1230.15
# best_prompt_performance: 1230.15
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_192228.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.9063979802367  # OPT_PARAM: {"initial": 420.9063979802367, "min": 380, "max": 480, "type": "float"}
    safety_stock = 42.0  # OPT_PARAM: {"initial": 42.0, "min": 30, "max": 55, "type": "float"}
    demand_forecast = 98.03596809968414  # OPT_PARAM: {"initial": 98.03596809968414, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7325794770968019  # OPT_PARAM: {"initial": 0.7325794770968019, "min": 0.5, "max": 0.9, "type": "float"}
    order_threshold = 0.472927165223083  # OPT_PARAM: {"initial": 0.472927165223083, "min": 0.1, "max": 0.5, "type": "float"}

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
