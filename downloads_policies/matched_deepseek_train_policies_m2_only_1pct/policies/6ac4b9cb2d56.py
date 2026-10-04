# policy_hash: 6ac4b9cb2d56e8cf486d7a4d262407f7e83349979fdce4a2c47082b5b07ca901
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 3894.43
# best_prompt_performance: 3892.93
# best_rel_error_pct: 0.038517
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_070959.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 506.9564661655399  # OPT_PARAM: {"initial": 506.9564661655399, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 192.9361967972107  # OPT_PARAM: {"initial": 192.9361967972107, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Update demand estimate using exponential smoothing
    # Use recent pipeline arrivals as proxy for recent demand
    if pipeline_orders[0] > 0:  # Only update when we had arrivals
        demand_estimate = (1 - smoothing_factor) * demand_estimate + smoothing_factor * pipeline_orders[0]

    # Dynamic base stock adjustment based on demand estimate
    dynamic_base = base_stock * (demand_estimate / 100.0)

    # Calculate order-up-to level with safety stock
    order_up_to = max(dynamic_base, demand_estimate * 4 + safety_stock)  # 4 periods of coverage

    # Calculate order amount
    order_amount = 0.5  # Optimized

    # Add small adjustment based on pipeline imbalance
    pipeline_imbalance = sum(pipeline_orders[i] for i in range(len(pipeline_orders))) / len(pipeline_orders)
    if pipeline_imbalance < demand_estimate * 0.8:
        order_amount = max(order_amount, demand_estimate * 0.5)  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 1.0, "type": "float"}

    return order_amount
