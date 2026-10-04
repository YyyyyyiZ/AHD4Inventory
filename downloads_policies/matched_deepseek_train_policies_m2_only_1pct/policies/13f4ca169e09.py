# policy_hash: 13f4ca169e09630dacfe1f93858f651bace54d7652d114b71aac2c0e1f0a7d90
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 5518.26
# best_prompt_performance: 5517.41
# best_rel_error_pct: 0.015403
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_002221.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 429.1207335332621  # OPT_PARAM: {"initial": 429.1207335332621, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 0.002122612206304484  # OPT_PARAM: {"initial": 0.002122612206304484, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 51.29999633515964  # OPT_PARAM: {"initial": 51.29999633515964, "min": 50, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall considering lead time
    lead_time = len(pipeline_orders)
    expected_demand_during_lead_time = demand_forecast * lead_time

    # Adjust base stock based on pipeline coverage
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order amount with smoothing
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Add demand forecast adjustment
    order_amount = max(order_amount, demand_forecast)

    return order_amount
