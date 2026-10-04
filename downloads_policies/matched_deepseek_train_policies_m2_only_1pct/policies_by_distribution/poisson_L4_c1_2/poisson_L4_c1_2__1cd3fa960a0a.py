# policy_hash: 1cd3fa960a0adacefa131427a841466f7dfa1409d7f6c2ef6735912cc16e21ab
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 780.5
# best_prompt_performance: 780.36
# best_rel_error_pct: 0.017937
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_080331.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 272.5826554673778  # OPT_PARAM: {"initial": 272.5826554673778, "min": 250, "max": 350, "type": "float"}
    safety_stock = 39.619778599950166  # OPT_PARAM: {"initial": 39.619778599950166, "min": 30, "max": 70, "type": "float"}
    demand_forecast = 96.65018060938031  # OPT_PARAM: {"initial": 96.65018060938031, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.41813756180479356  # OPT_PARAM: {"initial": 0.41813756180479356, "min": 0.3, "max": 1.0, "type": "float"}
    inventory_weight = 1.0350447532283082  # OPT_PARAM: {"initial": 1.0350447532283082, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate total pipeline
    total_pipeline = sum(pipeline_orders)

    # Weight imminent arrivals more heavily
    weighted_pipeline = pipeline_orders[0] * pipeline_weight + sum(pipeline_orders[1:]) * (1 - pipeline_weight)

    # Calculate effective inventory position with weighted components
    effective_position = on_hand_inventory * inventory_weight + weighted_pipeline

    # Dynamic target based on safety stock
    target_inventory = base_stock + safety_stock

    # Order calculation with pipeline consideration
    raw_order = max(0, target_inventory - effective_position)

    # Apply smoothing with demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
