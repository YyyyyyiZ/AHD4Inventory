# policy_hash: 88f626f03338683908e89e310dd5ee6ce54c0c961a2a5ed8eaecbef8a81ef70a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 35
# source_prompt_files: 1
# best_target_performance: 744.89
# best_prompt_performance: 744.89
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_102202.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 356.90371283692326  # OPT_PARAM: {"initial": 356.90371283692326, "min": 200, "max": 600, "type": "float"}
    safety_stock = 31.903712836916153  # OPT_PARAM: {"initial": 31.903712836916153, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand based on lead time
    lead_time = len(pipeline_orders)
    estimated_demand = 106.9037128369157  # OPT_PARAM: {"initial": 106.9037128369157, "min": 50, "max": 150, "type": "float"}

    # Calculate target inventory
    target_inventory = base_stock + safety_stock + estimated_demand

    # Calculate order amount
    order_amount = max(0, target_inventory - net_inventory)

    # Apply ordering constraints
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 20, "type": "float"}
    max_order = 96.20571855131226  # OPT_PARAM: {"initial": 96.20571855131226, "min": 50, "max": 300, "type": "float"}

    if order_amount < min_order:
        order_amount = 0
    elif order_amount > max_order:
        order_amount = max_order

    return order_amount
