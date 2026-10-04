# policy_hash: ddd0a86c2affe16ba6bb868c8250b068f7db19f2d664abe735adac6f8ac9869f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2191.21
# best_prompt_performance: 2191.21
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_002659.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 493.4195324661962  # OPT_PARAM: {"initial": 493.4195324661962, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 40.420722153857355  # OPT_PARAM: {"initial": 40.420722153857355, "min": 0, "max": 200, "type": "float"}
    demand_adjustment = 0.738743220437131  # OPT_PARAM: {"initial": 0.738743220437131, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate expected demand from pipeline (assuming pipeline reflects recent ordering)
    if len(pipeline_orders) > 0:
        recent_orders = pipeline_orders[-2:] if len(pipeline_orders) >= 2 else pipeline_orders
        avg_recent_order = sum(recent_orders) / len(recent_orders)
        expected_demand = avg_recent_order * demand_adjustment
    else:
        expected_demand = 100.0  # Default fallback

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock + expected_demand

    # Calculate order amount with smoothing
    order_gap = target_inventory - inventory_position
    if order_gap > 0:
        # Smooth ordering to avoid large fluctuations
        smoothing_factor = 0.47497350740232425  # OPT_PARAM: {"initial": 0.47497350740232425, "min": 0.1, "max": 1.0, "type": "float"}
        order_amount = max(0, smoothing_factor * order_gap)
    else:
        order_amount = 0

    # Ensure integer order amount
    return order_amount
