# policy_hash: f8726967be9a9c30090bf11b663b5b922c9bb29cfad94f4f7a4230a89fa2e0d6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 1136.41
# best_prompt_performance: 1136.41
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233704.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 318.0758972786734  # OPT_PARAM: {"initial": 318.0758972786734, "min": 250, "max": 400, "type": "float"}
    safety_stock = 42.982460262819565  # OPT_PARAM: {"initial": 42.982460262819565, "min": 20, "max": 60, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Better demand estimation using all pipeline orders
    if len(pipeline_orders) >= 2:
        # Weight recent arrivals more heavily
        recent_demand_estimate = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.4, "max": 0.8, "type": "float"}
    else:
        recent_demand_estimate = 100.0

    # Dynamic base stock adjustment with finer granularity
    adjusted_base_stock = base_stock + safety_stock

    if recent_demand_estimate > 115:
        adjusted_base_stock += 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}
    elif recent_demand_estimate > 105:
        adjusted_base_stock += 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 15, "type": "float"}
    elif recent_demand_estimate < 85:
        adjusted_base_stock -= 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 25, "type": "float"}
    elif recent_demand_estimate < 95:
        adjusted_base_stock -= 5.0  # OPT_PARAM: {"initial": 5.0, "min": 0, "max": 10, "type": "float"}

    # Calculate order amount
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # More aggressive smoothing for large orders
    if raw_order > 200:
        smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.2, "max": 0.6, "type": "float"}
        order_amount = raw_order * smoothing_factor
    elif raw_order > 100:
        smoothing_factor = 0.65  # OPT_PARAM: {"initial": 0.65, "min": 0.4, "max": 0.8, "type": "float"}
        order_amount = raw_order * smoothing_factor
    else:
        order_amount = raw_order

    # Round to nearest integer
    return order_amount
