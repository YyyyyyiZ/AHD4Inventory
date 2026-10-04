# policy_hash: caac08d63e6fa11caddf83ba5c85a5d2cab34bbc26c4e6922db9120dba90f032
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 7239.99
# best_prompt_performance: 7237.69
# best_rel_error_pct: 0.031768
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_034134.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 287.67088087946115  # OPT_PARAM: {"initial": 287.67088087946115, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 47.00474014422661  # OPT_PARAM: {"initial": 47.00474014422661, "min": 0, "max": 200, "type": "float"}
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

    # Round to nearest integer (since order amount should be integer)
    return order_amount
