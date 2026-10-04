# policy_hash: 2ee15b7aeee746ae839bd1624a860c9d1709ad50962608bd155ad0c9e76a9590
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 3300.89
# best_prompt_performance: 3298.44
# best_rel_error_pct: 0.074222
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_084113.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 624.8530544764235  # OPT_PARAM: {"initial": 624.8530544764235, "min": 500, "max": 900, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    order_threshold = 20.1  # OPT_PARAM: {"initial": 20.1, "min": 5, "max": 40, "type": "float"}
    safety_stock = 75.15452326291812  # OPT_PARAM: {"initial": 75.15452326291812, "min": 50, "max": 200, "type": "float"}
    demand_adjustment = 0.9679242340060746  # OPT_PARAM: {"initial": 0.9679242340060746, "min": 0.9, "max": 1.2, "type": "float"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on recent pipeline pattern
    recent_pipeline = sum(pipeline_orders[:3]) if len(pipeline_orders) >= 3 else sum(pipeline_orders)
    if recent_pipeline < 200:
        adjusted_base_stock = base_stock * demand_adjustment
    else:
        adjusted_base_stock = base_stock

    # Add safety stock component
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply ordering threshold
    if order_amount < order_threshold:
        order_amount = 0

    return order_amount
