# policy_hash: b27326cd168519b9c778f7dc71c3e792484c7d49ce6769290fd4c274796d4686
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 6235.26
# best_prompt_performance: 6235.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_092608.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 433.4296714580751  # OPT_PARAM: {"initial": 433.4296714580751, "min": 300, "max": 600, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    safety_stock = 43.42967145807159  # OPT_PARAM: {"initial": 43.42967145807159, "min": 20, "max": 120, "type": "float"}
    demand_anticipation_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}
    pipeline_decay = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate weighted pipeline with decay (more weight to near-term arrivals)
    weighted_pipeline = 0.0
    weight = 1.0
    for order in pipeline_orders:
        weighted_pipeline += order * weight
        weight *= pipeline_decay

    # Calculate effective pipeline
    effective_pipeline = weighted_pipeline * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock with safety stock and demand anticipation
    adjusted_base_stock = base_stock + safety_stock
    adjusted_base_stock = adjusted_base_stock * demand_anticipation_factor

    # Calculate raw order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply smoothing with threshold to avoid small orders
    if raw_order > 10:  # Minimum order threshold
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
