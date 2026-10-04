# policy_hash: f324b895fcae3a03604dbdda4e0e405b8fc5f29d67990cddf4e54fcaff8cc666
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3315.82
# best_prompt_performance: 3314.37
# best_rel_error_pct: 0.043730
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_083346.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 691.2884589331811  # OPT_PARAM: {"initial": 691.2884589331811, "min": 500, "max": 900, "type": "float"}
    pipeline_weight = 0.9823513518391086  # OPT_PARAM: {"initial": 0.9823513518391086, "min": 0.7, "max": 1.0, "type": "float"}
    order_threshold = 15.1  # OPT_PARAM: {"initial": 15.1, "min": 5, "max": 40, "type": "float"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(pipeline_orders) * pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate order amount
    order_amount = max(0, base_stock - inventory_position)

    # Apply ordering threshold
    if order_amount < order_threshold:
        order_amount = 0

    return order_amount
