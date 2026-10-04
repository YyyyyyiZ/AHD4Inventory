# policy_hash: 95201fdc9deae0b33af7de70a38ae2c6706bb217bba697d01966ac66e2635825
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2043.23
# best_prompt_performance: 2040.9
# best_rel_error_pct: 0.114035
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044339.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 519.9983551268418  # OPT_PARAM: {"initial": 519.9983551268418, "min": 300, "max": 700, "type": "float"}
    safety_stock = 34.99835512684195  # OPT_PARAM: {"initial": 34.99835512684195, "min": 0, "max": 100, "type": "float"}
    smoothing_factor = 0.6294883994609657  # OPT_PARAM: {"initial": 0.6294883994609657, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with dynamic adjustment
    # Use pipeline information to anticipate future needs
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        # Reduce target when pipeline is full
        pipeline_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
        adjusted_base = base_stock * pipeline_factor
    else:
        adjusted_base = base_stock

    target_inventory = adjusted_base + safety_stock

    # Calculate order quantity
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Ensure minimum order quantity for efficiency
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}
    if 0 < order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
