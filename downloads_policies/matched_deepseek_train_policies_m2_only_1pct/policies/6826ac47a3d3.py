# policy_hash: 6826ac47a3d3fc336ef0ef0dc553239a1ff3d37553172211104fead7c6c3c177
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 11016.86
# best_prompt_performance: 11016.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_090313.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 483.3726025279026  # OPT_PARAM: {"initial": 483.3726025279026, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.8226579621164967  # OPT_PARAM: {"initial": 0.8226579621164967, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.22985689679834292  # OPT_PARAM: {"initial": 0.22985689679834292, "min": 0.1, "max": 0.4, "type": "float"}
    safety_stock = 118.37260252790217  # OPT_PARAM: {"initial": 118.37260252790217, "min": 50, "max": 250, "type": "float"}
    demand_anticipation = 0.23653987131735502  # OPT_PARAM: {"initial": 0.23653987131735502, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_threshold = 0.381672803464575  # OPT_PARAM: {"initial": 0.381672803464575, "min": 0.2, "max": 0.6, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjusted base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to amount
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply demand anticipation only when pipeline is very low
    if sum(pipeline_orders) < pipeline_threshold * adjusted_base_stock:
        order_up_to *= (1 + demand_anticipation)

    # Apply consistent smoothing
    order_amount = smoothing_factor * order_up_to

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
