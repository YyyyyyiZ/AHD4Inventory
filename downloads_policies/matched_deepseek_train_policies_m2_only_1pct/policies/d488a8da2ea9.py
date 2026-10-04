# policy_hash: d488a8da2ea9783eb9479c4f0c2ac7243af2c4b04fe2692211b7fd7166381693
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 2270.84
# best_prompt_performance: 2270.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_113904.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 594.9189518067652  # OPT_PARAM: {"initial": 594.9189518067652, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 45.33877570759674  # OPT_PARAM: {"initial": 45.33877570759674, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.10659680904122845  # OPT_PARAM: {"initial": 0.10659680904122845, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_lead_time = 6  # Fixed lead time

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time (using historical average as proxy)
    # Since we can't access historical data in the policy, we use a fixed forecast
    # This value represents the average demand per period
    avg_demand_per_period = 95.42291351505268  # OPT_PARAM: {"initial": 95.42291351505268, "min": 50, "max": 200, "type": "float"}

    # Expected demand during lead time + review period
    expected_demand_during_lead_time = avg_demand_per_period * pipeline_lead_time * demand_forecast_factor

    # Calculate target inventory level
    target_inventory = expected_demand_during_lead_time + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply order smoothing to reduce volatility
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * avg_demand_per_period

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
