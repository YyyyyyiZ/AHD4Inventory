# policy_hash: 2aec807edc44593be06efe7aee9fda359d78d4e88aa1dd345549faac52cb2958
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 32
# source_prompt_files: 1
# best_target_performance: 1916.13
# best_prompt_performance: 1916.13
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_034959.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 614.2634545167023  # OPT_PARAM: {"initial": 614.2634545167023, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 22.021310587360684  # OPT_PARAM: {"initial": 22.021310587360684, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 84.32889063009503  # OPT_PARAM: {"initial": 84.32889063009503, "min": 50, "max": 150, "type": "float"}
    pipeline_weight = 0.9442538402271937  # OPT_PARAM: {"initial": 0.9442538402271937, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on pipeline status
    adjusted_base = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Smooth ordering by considering forecast
    if order_amount > 0:
        order_amount = max(demand_forecast * 0.5, min(order_amount, demand_forecast * 2.0))

    return order_amount
