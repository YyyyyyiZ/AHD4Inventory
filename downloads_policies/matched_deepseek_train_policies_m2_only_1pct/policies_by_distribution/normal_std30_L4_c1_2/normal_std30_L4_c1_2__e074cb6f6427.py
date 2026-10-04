# policy_hash: e074cb6f6427c2a3807525409329a37ba5cabc10ea6edbc95e24e8f2cc8c6368
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_2
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 2142.06
# best_prompt_performance: 2142.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_075059.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 423.8650647743375  # OPT_PARAM: {"initial": 423.8650647743375, "min": 300, "max": 600, "type": "float"}
    safety_stock = 28.865064774337856  # OPT_PARAM: {"initial": 28.865064774337856, "min": 10, "max": 80, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Target inventory position
    target_position = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply order smoothing with tighter bounds
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}
    max_order_jump = 172.54124613637146  # OPT_PARAM: {"initial": 172.54124613637146, "min": 80, "max": 200, "type": "float"}

    if order_amount > 0:
        order_amount = min(order_amount, max_order_jump)
        # Apply stronger smoothing to reduce volatility
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * (max_order_jump * 0.5)

    # Round to nearest integer
    return order_amount
