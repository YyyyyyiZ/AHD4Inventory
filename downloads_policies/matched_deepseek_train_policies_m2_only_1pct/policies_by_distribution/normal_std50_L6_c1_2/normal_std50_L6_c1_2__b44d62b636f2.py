# policy_hash: b44d62b636f257861ca5d76cbefa98aaede6df5bb724f837b25f7c41051a71a6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 27
# source_prompt_files: 1
# best_target_performance: 3746.45
# best_prompt_performance: 3746.45
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_214258.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 570.9676310013208  # OPT_PARAM: {"initial": 570.9676310013208, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 86.25975840895606  # OPT_PARAM: {"initial": 86.25975840895606, "min": 0, "max": 200, "type": "float"}
    pipeline_lead_time = 6  # fixed lead time

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Use fixed forecast based on historical demand mean
    forecast = 96.77594110355973  # OPT_PARAM: {"initial": 96.77594110355973, "min": 50, "max": 200, "type": "float"}

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - net_inventory)

    # Apply order smoothing
    max_order = 81.20265104024182  # OPT_PARAM: {"initial": 81.20265104024182, "min": 50, "max": 300, "type": "float"}
    min_order = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 50, "type": "float"}

    # Smooth ordering: if order_amount is small, consider not ordering
    if order_amount < min_order:
        order_amount = 0
    else:
        order_amount = min(order_amount, max_order)

    return order_amount
