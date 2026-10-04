# policy_hash: e7dfe232753c075ba184e0a47f0abf7ed2df38cc1a66a7eb2607f1e67712f65b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2234.12
# best_prompt_performance: 2236.66
# best_rel_error_pct: 0.113691
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091613.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 635.9503191768238  # OPT_PARAM: {"initial": 635.9503191768238, "min": 400, "max": 900, "type": "float"}
    safety_stock = 73.2052647615749  # OPT_PARAM: {"initial": 73.2052647615749, "min": 50, "max": 200, "type": "float"}
    demand_forecast = 96.0820321912981  # OPT_PARAM: {"initial": 96.0820321912981, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.8681336632014982  # OPT_PARAM: {"initial": 0.8681336632014982, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position with full pipeline consideration
    full_pipeline = sum(pipeline_orders)
    inventory_position = on_hand_inventory + full_pipeline * pipeline_weight

    # Calculate target order with clearer logic
    target_inventory = base_stock + safety_stock
    deficit = target_inventory - inventory_position

    # Add demand forecast
    order_target = max(0, deficit + demand_forecast)

    # Apply adjustment with stronger smoothing
    order_amount = max(0, order_target * adjustment_factor)

    # Round to nearest integer
    return order_amount
