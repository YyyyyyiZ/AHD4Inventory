# policy_hash: 1b6a71f2eac7dca92612a5921b9c84b389456da3e0b2e6495425602b609e2221
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 735.2
# best_prompt_performance: 735.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_025913.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 509.02524863770674  # OPT_PARAM: {"initial": 509.02524863770674, "min": 450, "max": 650, "type": "float"}
    lead_time = 4

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate order amount
    order_amount = max(0, base_stock - net_inventory)

    # Apply dynamic ordering limits based on demand forecast
    max_order = 97.07619741577733  # OPT_PARAM: {"initial": 97.07619741577733, "min": 90, "max": 180, "type": "float"}
    min_order = 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 15, "type": "float"}

    # Smooth ordering with proportional adjustment
    smoothing_factor = 0.7109658662500069  # OPT_PARAM: {"initial": 0.7109658662500069, "min": 0.3, "max": 1.0, "type": "float"}
    order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * max_order / 2

    # Cap the order amount
    if order_amount > max_order:
        order_amount = max_order
    elif order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer
    return order_amount
