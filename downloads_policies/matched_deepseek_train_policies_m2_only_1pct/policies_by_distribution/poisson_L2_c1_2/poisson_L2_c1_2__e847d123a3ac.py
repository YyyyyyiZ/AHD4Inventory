# policy_hash: e847d123a3ac38f76ae495177b75cffe02208f9dbd5d4b7b99fa5ca27f1a2dec
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 951.52
# best_prompt_performance: 949.96
# best_rel_error_pct: 0.163948
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_064815.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 304.8085141702039  # OPT_PARAM: {"initial": 304.8085141702039, "min": 280, "max": 320, "type": "float"}
    safety_stock = 19.962562825265884  # OPT_PARAM: {"initial": 19.962562825265884, "min": 15, "max": 25, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.3, "type": "float"}
    adjustment_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected lead time demand
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Adjust for pipeline orders with simpler weighting
    pipeline_adjustment = sum(pipeline_orders) * pipeline_weight

    # Calculate order amount
    order_amount = max(0, (target_position - net_inventory + pipeline_adjustment) * adjustment_factor)

    # Round to nearest integer
    return order_amount
