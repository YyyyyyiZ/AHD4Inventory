# policy_hash: 082c91d8fd35e92f9e5720391a66a1883e3d0578aae08aea45c39b0e28c94f37
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 50
# source_prompt_files: 1
# best_target_performance: 11047.91
# best_prompt_performance: 11047.78
# best_rel_error_pct: 0.001177
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044917.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 443.32286268575774  # OPT_PARAM: {"initial": 443.32286268575774, "min": 300, "max": 800, "type": "float"}
    demand_estimate = 102.39865198786123  # OPT_PARAM: {"initial": 102.39865198786123, "min": 80, "max": 200, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    buffer_multiplier = 0.5418245179451103  # OPT_PARAM: {"initial": 0.5418245179451103, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_threshold = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = base_stock + expected_lead_time_demand * buffer_multiplier

    # Calculate order needed to reach target
    order_needed = target_position - inventory_position

    # Apply smoothing and ensure non-negative order
    if order_needed > 0:
        # Smooth order adjustment
        order_amount = max(0, smoothing_factor * order_needed)
        # Order at least expected demand when significantly below target
        if inventory_position < target_position * min_order_threshold:
            order_amount = max(order_amount, demand_estimate)
    else:
        order_amount = 0

    return order_amount
