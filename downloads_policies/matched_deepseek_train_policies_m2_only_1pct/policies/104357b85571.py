# policy_hash: 104357b85571002919fe8c8139e23b91f971f9bb2de9241c5a66d9c220c9dc88
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 6045.04
# best_prompt_performance: 6045.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_095026.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 485.0059263492611  # OPT_PARAM: {"initial": 485.0059263492611, "min": 400, "max": 600, "type": "float"}
    pipeline_weight = 0.9179257777850786  # OPT_PARAM: {"initial": 0.9179257777850786, "min": 0.85, "max": 1.0, "type": "float"}
    smoothing_factor = 0.14703682540725507  # OPT_PARAM: {"initial": 0.14703682540725507, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock = 65.10592634926105  # OPT_PARAM: {"initial": 65.10592634926105, "min": 40, "max": 100, "type": "float"}
    demand_buffer = 1.15  # OPT_PARAM: {"initial": 1.15, "min": 1.0, "max": 1.3, "type": "float"}
    min_order_threshold = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    recent_demand_weight = 0.5911104762217653  # OPT_PARAM: {"initial": 0.5911104762217653, "min": 0.3, "max": 0.8, "type": "float"}
    pipeline_cap_factor = 0.6940736508145101  # OPT_PARAM: {"initial": 0.6940736508145101, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate effective pipeline with cap to avoid over-weighting
    total_pipeline = sum(pipeline_orders)
    capped_pipeline = total_pipeline * pipeline_cap_factor
    effective_pipeline = capped_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic target based on recent demand signal
    recent_demand_signal = 0
    if len(pipeline_orders) >= 2:
        recent_demand_signal = (pipeline_orders[0] * (1 - recent_demand_weight) +
                               pipeline_orders[1] * recent_demand_weight)

    # Adjust base stock upward for higher recent demand
    adjusted_base = base_stock + min(50, recent_demand_signal * 0.3)
    target_inventory = adjusted_base + safety_stock

    # Calculate raw order amount
    raw_order = max(0, target_inventory - inventory_position)

    # Apply demand-based adjustment
    if raw_order > 0 and recent_demand_signal > 0:
        demand_adjusted = raw_order * demand_buffer
        # More conservative cap than before
        raw_order = min(demand_adjusted, raw_order * 1.1)

    # Apply smoothing with minimum order threshold
    if raw_order > min_order_threshold:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
