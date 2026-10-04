# policy_hash: 4ba5a8e58137ead46bee4605cbb159e6ab4d76be2b270b55a06bdce18087f2c2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2039.82
# best_prompt_performance: 2039.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234400.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 440.85356525287347  # OPT_PARAM: {"initial": 440.85356525287347, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 37.7107065289881  # OPT_PARAM: {"initial": 37.7107065289881, "min": 0, "max": 200, "type": "float"}
    pipeline_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum > 0:
        pipeline_avg = pipeline_sum / len(pipeline_orders)
        pipeline_variability = sum(abs(p - pipeline_avg) for p in pipeline_orders) / pipeline_sum
        adjusted_base = base_stock * (1 + pipeline_variability * pipeline_factor)
    else:
        adjusted_base = base_stock

    # Add safety stock
    target_inventory = adjusted_base + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
