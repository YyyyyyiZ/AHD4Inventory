# policy_hash: b9702a576012df682fc37aaea9f5982f0d746f8bd769125401ca19e33f5ca75d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5548.14
# best_prompt_performance: 5541.64
# best_rel_error_pct: 0.117156
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_225404.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 502.3181555150379  # OPT_PARAM: {"initial": 502.3181555150379, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 18.365985373070902  # OPT_PARAM: {"initial": 18.365985373070902, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on pipeline orders (as proxy for recent demand)
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        expected_demand = avg_pipeline * demand_forecast_factor
    else:
        expected_demand = 0

    # Adjust base stock based on expected demand
    adjusted_base_stock = base_stock + expected_demand

    # Calculate target inventory position
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
