# policy_hash: 920905be81324448e515b4605fd4d6bce4809756eb94871ef29e9cd6af66a3a0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1542.24
# best_prompt_performance: 1532.1
# best_rel_error_pct: 0.657485
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_072817.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    reorder_point = 500.0  # OPT_PARAM: {"initial": 500.0, "min": 200, "max": 500, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = 4 * demand_forecast  # L=4

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + safety_stock

    # Use the larger of base_stock and target_inventory as order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount only if inventory position is below reorder point
    if inventory_position < reorder_point:
        order_amount = max(0, order_up_to - inventory_position)
    else:
        order_amount = 0

    # Apply smoothing to reduce order volatility
    if order_amount > 0:
        order_amount = int(order_amount * smoothing_factor + 0.5)

    return order_amount
