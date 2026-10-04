# policy_hash: fbc53e911ccf804e3dfe8bb9ea9269ccb726c6618d04c463d045e078f9fb362d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 3114.85
# best_prompt_performance: 3114.85
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_005858.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 783.8148782837767  # OPT_PARAM: {"initial": 783.8148782837767, "min": 400, "max": 900, "type": "float"}
    safety_stock = 79.72396112098846  # OPT_PARAM: {"initial": 79.72396112098846, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Blend base_stock and target_inventory based on pipeline status
    effective_base = (pipeline_weight * base_stock +
                     (1 - pipeline_weight) * target_inventory)

    # Calculate order amount
    order_amount = max(0, adjustment_factor * (effective_base - inventory_position))

    # Round to nearest integer
    return order_amount
