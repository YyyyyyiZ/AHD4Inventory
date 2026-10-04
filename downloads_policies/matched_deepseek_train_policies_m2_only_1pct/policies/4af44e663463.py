# policy_hash: 4af44e66346310e5b68651946b91f70cd04325c3976d0fe7f6d9ce76e0e5ad8c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 6243.0
# best_prompt_performance: 6243.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_012549.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 329.5097628658834  # OPT_PARAM: {"initial": 329.5097628658834, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 22.5496054232458  # OPT_PARAM: {"initial": 22.5496054232458, "min": 0, "max": 200, "type": "float"}
    pipeline_coverage = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + sum(pipeline_orders) * pipeline_coverage

    # Adjust base stock based on safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - effective_inventory)

    # Apply smoothing to avoid extreme orders
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = order_amount * smoothing_factor

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
