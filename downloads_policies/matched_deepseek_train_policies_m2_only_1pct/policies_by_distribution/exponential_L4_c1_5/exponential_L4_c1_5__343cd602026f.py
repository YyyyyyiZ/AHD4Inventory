# policy_hash: 343cd602026f485b71800e78943bb1afdd386ba11e342dd90130494ab5b3517d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 11
# source_prompt_files: 2
# best_target_performance: 11019.98
# best_prompt_performance: 11019.98
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050828.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 378.94224727856  # OPT_PARAM: {"initial": 378.94224727856, "min": 200, "max": 500, "type": "float"}
    safety_stock = 115.67569472240785  # OPT_PARAM: {"initial": 115.67569472240785, "min": 50, "max": 200, "type": "float"}
    demand_forecast_factor = 1.1472083536622482  # OPT_PARAM: {"initial": 1.1472083536622482, "min": 0.8, "max": 1.3, "type": "float"}
    order_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}
    pipeline_weight = 0.4764304288024482  # OPT_PARAM: {"initial": 0.4764304288024482, "min": 0.4, "max": 0.8, "type": "float"}
    lost_sales_weight = 2.625463227774727  # OPT_PARAM: {"initial": 2.625463227774727, "min": 2.0, "max": 3.0, "type": "float"}
    demand_volatility_factor = 0.8415472705514198  # OPT_PARAM: {"initial": 0.8415472705514198, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Improved demand forecast using weighted pipeline orders
    if len(pipeline_orders) > 0:
        # Use linear weights (more weight to recent orders)
        weights = []
        for i in range(len(pipeline_orders)):
            weight = (len(pipeline_orders) - i)  # Linear weights
            weights.append(weight)
        weights = [w/sum(weights) for w in weights]
        forecast = sum(w * d for w, d in zip(weights, pipeline_orders))
        forecast = forecast * demand_forecast_factor
    else:
        forecast = 0

    # Adjust base stock based on pipeline status
    pipeline_sum = sum(pipeline_orders)
    pipeline_adjustment = pipeline_sum * pipeline_weight

    # Adjust safety stock based on cost ratio and demand volatility
    adjusted_safety = safety_stock * lost_sales_weight * demand_volatility_factor

    # Target inventory level with pipeline consideration
    target_inventory = base_stock + adjusted_safety + forecast - pipeline_adjustment

    # Calculate order needed
    order_needed = max(0, target_inventory - inventory_position)

    # Apply order smoothing with threshold
    if order_needed > 0:
        order_amount = order_needed * order_smoothing
    else:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
