# policy_hash: 9d18f195730c0d3e3c3afab792d5d711960132e4804949d3f5aa51f982e3bccd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 743.9
# best_prompt_performance: 743.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_081000.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 377.9385707527889  # OPT_PARAM: {"initial": 377.9385707527889, "min": 300, "max": 450, "type": "float"}
    safety_stock = 70.58729740447725  # OPT_PARAM: {"initial": 70.58729740447725, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 96.196655106841  # OPT_PARAM: {"initial": 96.196655106841, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate weighted inventory position
    inventory_position = on_hand_inventory
    for i, p in enumerate(pipeline_orders):
        inventory_position += p * (pipeline_weight ** (i + 1))

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Apply base_stock as upper bound
    order_up_to = min(base_stock, target_inventory)

    # Calculate order quantity
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce volatility
    if order_amount > 0:
        smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast
        order_amount = min(order_amount, smoothed_order)

    return order_amount
