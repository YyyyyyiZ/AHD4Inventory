# policy_hash: 3e5c939528ef25ce69b5af8447a59a48fa96d3e69dc0138608c6203ddcc57c71
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1726.62
# best_prompt_performance: 1726.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035002.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 432.4904024262976  # OPT_PARAM: {"initial": 432.4904024262976, "min": 100, "max": 800, "type": "float"}
    safety_stock = 47.59040242630235  # OPT_PARAM: {"initial": 47.59040242630235, "min": 0, "max": 200, "type": "float"}
    pipeline_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 1.376393578743695  # OPT_PARAM: {"initial": 1.376393578743695, "min": 0, "max": 50, "type": "float"}

    # Calculate effective pipeline with discount factor
    effective_pipeline = sum(pipeline_orders) * pipeline_factor

    # Calculate inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic target based on pipeline status
    pipeline_sum = sum(pipeline_orders)
    if pipeline_sum < 300:
        target_adjustment = demand_buffer
    else:
        target_adjustment = -demand_buffer

    target = base_stock + safety_stock + target_adjustment

    # Calculate order amount
    order_amount = max(0, target - inventory_position)

    # Round to nearest integer
    return order_amount
