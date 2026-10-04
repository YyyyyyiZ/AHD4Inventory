# policy_hash: 64f72cc2a39b7fba983dfcbd7adc5f09cdda7abd083606d77187842bd38743d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 6262.06
# best_prompt_performance: 6262.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013810.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 200, "max": 450, "type": "float"}
    safety_stock = 124.2796873807525  # OPT_PARAM: {"initial": 124.2796873807525, "min": 80, "max": 200, "type": "float"}
    demand_estimate = 102.6794650540619  # OPT_PARAM: {"initial": 102.6794650540619, "min": 80, "max": 150, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate effective pipeline (weighted sum)
    effective_pipeline = sum(p * pipeline_weight for p in pipeline_orders)

    # Calculate target inventory level
    target_level = max(base_stock, lead_time_demand + safety_stock - effective_pipeline)

    # Calculate order amount with smoothing
    raw_order = target_level - inventory_position
    order_amount = raw_order * adjustment_smoothing

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
