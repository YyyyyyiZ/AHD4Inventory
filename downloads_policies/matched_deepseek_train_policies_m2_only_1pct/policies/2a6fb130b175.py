# policy_hash: 2a6fb130b175e9c8b884c326701f547521866fb80889b97f42bb79c6fd254825
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 21
# source_prompt_files: 1
# best_target_performance: 1223.82
# best_prompt_performance: 1223.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_193649.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 410.0  # OPT_PARAM: {"initial": 410.0, "min": 380, "max": 450, "type": "float"}
    safety_stock = 31.756124008298013  # OPT_PARAM: {"initial": 31.756124008298013, "min": 25, "max": 45, "type": "float"}
    demand_forecast = 97.62722308752689  # OPT_PARAM: {"initial": 97.62722308752689, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.7247506585366578  # OPT_PARAM: {"initial": 0.7247506585366578, "min": 0.7, "max": 1.0, "type": "float"}
    order_threshold = 0.4840343547752335  # OPT_PARAM: {"initial": 0.4840343547752335, "min": 0.1, "max": 0.5, "type": "float"}
    lead_time = 4  # Fixed parameter

    # Calculate effective inventory position with discounted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Dynamic target based on both base stock and safety stock
    target_position = max(base_stock, expected_lead_time_demand + safety_stock)

    # Calculate raw order amount
    raw_order = max(0, target_position - inventory_position)

    # Apply smoothing with threshold
    if raw_order > order_threshold * demand_forecast:
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
