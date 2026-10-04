# policy_hash: 501a42e81aadbb8891745d72c2dae0ec3035825ee3abd13865cba9fddb99468e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 123
# source_prompt_files: 1
# best_target_performance: 11103.46
# best_prompt_performance: 11103.39
# best_rel_error_pct: 0.000630
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_063511.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.4359531028647  # OPT_PARAM: {"initial": 380.4359531028647, "min": 200, "max": 500, "type": "float"}
    safety_multiplier = 1.8763287964233135  # OPT_PARAM: {"initial": 1.8763287964233135, "min": 1.0, "max": 3.0, "type": "float"}
    pipeline_weight = 0.7959330044032894  # OPT_PARAM: {"initial": 0.7959330044032894, "min": 0.5, "max": 1.0, "type": "float"}
    smoothing = 0.14750362975857675  # OPT_PARAM: {"initial": 0.14750362975857675, "min": 0.1, "max": 0.5, "type": "float"}
    min_order = 19.918627917231678  # OPT_PARAM: {"initial": 19.918627917231678, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline coverage (emphasize near-term arrivals)
    weighted_pipeline = 0
    total_weight = 0
    L = len(pipeline_orders)
    for i, order in enumerate(pipeline_orders):
        # Higher weight for orders arriving sooner
        weight = (L - i) ** 1.5
        weighted_pipeline += order * weight
        total_weight += weight
    if total_weight > 0:
        weighted_pipeline = weighted_pipeline / total_weight * L

    # Target inventory position
    target_inventory = base_stock * safety_multiplier

    # Calculate order needed
    net_order = target_inventory - inventory_position + pipeline_weight * weighted_pipeline

    # Apply smoothing and ensure minimum order when needed
    if net_order > min_order:
        order_amount = max(min_order, net_order * smoothing)
    else:
        order_amount = 0

    return order_amount
