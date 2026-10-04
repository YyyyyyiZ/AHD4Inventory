# policy_hash: a83a3af57de916bfc504ba612a1ad53467e2e35950c6798df411ac1a6a754237
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 5881.8
# best_prompt_performance: 5881.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230254.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 181.8280872417236  # OPT_PARAM: {"initial": 181.8280872417236, "min": 100, "max": 300, "type": "float"}
    safety_factor = 3.0951304981614842  # OPT_PARAM: {"initial": 3.0951304981614842, "min": 1.5, "max": 4.0, "type": "float"}
    pipeline_weight = 0.9868913122701855  # OPT_PARAM: {"initial": 0.9868913122701855, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3114855204503092  # OPT_PARAM: {"initial": 0.3114855204503092, "min": 0.1, "max": 0.5, "type": "float"}
    demand_estimate_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use recent pipeline orders as demand estimate
    if len(pipeline_orders) >= 2:
        # Weight recent orders more heavily
        recent_weights = [0.3, 0.7] if len(pipeline_orders) >= 2 else [1.0]
        weighted_sum = sum(p * w for p, w in zip(pipeline_orders[-2:], recent_weights))
        demand_estimate = weighted_sum / sum(recent_weights) * demand_estimate_factor
        std_dev = max(demand_estimate * 0.3, 10.0)  # Minimum variability
    else:
        demand_estimate = base_stock * 0.5
        std_dev = base_stock * 0.25

    # Safety stock based on demand variability
    safety_stock = safety_factor * std_dev

    # Pipeline adjustment: order less when pipeline is full
    total_pipeline = sum(pipeline_orders)
    expected_pipeline = demand_estimate * len(pipeline_orders) * pipeline_weight
    pipeline_adjustment = max(0, expected_pipeline - total_pipeline) * 0.6

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock + pipeline_adjustment

    # Order needed to reach target
    order_needed = target_inventory - inventory_position

    # Smooth large orders
    if abs(order_needed) > demand_estimate * 0.5:
        smoothed_order = order_needed * smoothing_factor
    else:
        smoothed_order = order_needed

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
