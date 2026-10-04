# policy_hash: e9cbb226fca43098f0a9ce76cf921e03d6a96b896b7b3ddc3584071e644cdff3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_2
# matched_train_cells: 174
# source_prompt_files: 1
# best_target_performance: 2147.22
# best_prompt_performance: 2147.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_074228.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 384.8554101694159  # OPT_PARAM: {"initial": 384.8554101694159, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 11.550299643646918  # OPT_PARAM: {"initial": 11.550299643646918, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.49621840024540376  # OPT_PARAM: {"initial": 0.49621840024540376, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 3 pipeline arrivals as demand proxy
    recent_arrivals = pipeline_orders[:3]
    if len(recent_arrivals) > 0:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 0

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * avg_recent_demand

    # Calculate target inventory position
    target_position = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing to avoid extreme order variations
    smoothing_factor = 0.21228805070743126  # OPT_PARAM: {"initial": 0.21228805070743126, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        # Smooth large orders
        max_order_jump = 91.03178885034572  # OPT_PARAM: {"initial": 91.03178885034572, "min": 50, "max": 300, "type": "float"}
        order_amount = min(order_amount, max_order_jump)
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * max_order_jump

    return order_amount
