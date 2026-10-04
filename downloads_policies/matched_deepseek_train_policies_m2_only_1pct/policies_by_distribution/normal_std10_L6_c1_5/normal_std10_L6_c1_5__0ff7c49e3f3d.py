# policy_hash: 0ff7c49e3f3d0138efc577df614bb212e6e17f7d79147d3faab55c43e2b1fbdc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 1274.46
# best_prompt_performance: 1274.46
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_065854.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 748.0604106787265  # OPT_PARAM: {"initial": 748.0604106787265, "min": 500, "max": 1200, "type": "float"}
    safety_stock = 79.51623245076999  # OPT_PARAM: {"initial": 79.51623245076999, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 97.49547919993647  # OPT_PARAM: {"initial": 97.49547919993647, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}
    pipeline_weight = 0.6952800795430155  # OPT_PARAM: {"initial": 0.6952800795430155, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level with weighted adjustment
    target_inventory = expected_lead_time_demand + safety_stock

    # Blend base_stock and target_inventory based on pipeline status
    effective_base = base_stock * pipeline_weight + target_inventory * (1 - pipeline_weight)

    # Calculate order-up-to level
    order_up_to_level = max(effective_base, target_inventory)

    # Calculate order amount
    order_amount = max(0, order_up_to_level - inventory_position)

    # Apply smoothing only when order amount is significant
    if order_amount > demand_forecast * 0.5:
        order_amount = order_amount * smoothing_factor + (1 - smoothing_factor) * demand_forecast

    return order_amount
