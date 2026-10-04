# policy_hash: e05d4f5f6c5e57fde6115fe31c0535f9eb71f4431eda54e68e7e5c3407c50afb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 24217.9
# best_prompt_performance: 24217.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231007.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 324.93124999998804  # OPT_PARAM: {"initial": 324.93124999998804, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_variance = sum((q - sum(pipeline_orders)/len(pipeline_orders))**2 for q in pipeline_orders) if len(pipeline_orders) > 0 else 0
    pipeline_factor = max(0.5, 1.0 - pipeline_variance / 10000.0)  # OPT_PARAM: {"initial": 10000.0, "min": 1000, "max": 50000, "type": "float"}

    # Dynamic adjustment based on current inventory level
    if on_hand_inventory < safety_stock:
        urgency_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.0, "max": 2.0, "type": "float"}
    elif on_hand_inventory > base_stock * 0.7:
        urgency_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}
    else:
        urgency_factor = 1.0

    # Calculate target inventory position with adjustments
    adjusted_base_stock = base_stock * pipeline_factor * urgency_factor
    target_inventory = max(adjusted_base_stock, safety_stock * demand_forecast_factor)

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering to avoid extreme fluctuations
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if order_amount > avg_pipeline * 3.0:  # OPT_PARAM: {"initial": 3.0, "min": 1.5, "max": 5.0, "type": "float"}
            order_amount = avg_pipeline * 2.0  # OPT_PARAM: {"initial": 2.0, "min": 1.0, "max": 3.0, "type": "float"}

    return order_amount
