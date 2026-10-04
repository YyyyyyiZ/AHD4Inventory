# policy_hash: af33aff731577dfc2331422c5ace5b80ca671390b1290c8d076b7b9a56a1552c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 4017.2
# best_prompt_performance: 4017.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_133601.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 509.47063589086275  # OPT_PARAM: {"initial": 509.47063589086275, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 25.51846574889584  # OPT_PARAM: {"initial": 25.51846574889584, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective pipeline considering lead time weighting
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Order up to base_stock + safety_stock, adjusted by pipeline weighting
    order_amount = max(0, base_stock + safety_stock - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer since order amounts should be integers
    order_amount = int(round(order_amount))

    return order_amount
