# policy_hash: 699ce6ee881aba57a7ed7c3a8b4ceea7290303994865d7b3a2ddd26ed6cd3e6b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 3035.64
# best_prompt_performance: 3034.15
# best_rel_error_pct: 0.049084
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_095622.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 379.5764552058529  # OPT_PARAM: {"initial": 379.5764552058529, "min": 300, "max": 450, "type": "float"}
    safety_stock = 148.92915128121146  # OPT_PARAM: {"initial": 148.92915128121146, "min": 80, "max": 160, "type": "float"}
    demand_forecast = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 95, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    order_multiplier = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.3, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * lead_time

    # Calculate target inventory position
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate raw order amount with multiplier
    order_amount_raw = max(0, target_inventory - inventory_position) * order_multiplier

    # Apply smoothing with cap at base_stock
    order_amount = smoothing_factor * order_amount_raw + (1 - smoothing_factor) * min(order_amount_raw, base_stock)

    # Round to nearest integer
    return order_amount
