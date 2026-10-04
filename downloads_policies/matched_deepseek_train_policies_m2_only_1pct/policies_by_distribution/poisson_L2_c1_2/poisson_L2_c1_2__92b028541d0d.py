# policy_hash: 92b028541d0defc3bf3e62639449e1153ae8829f66f014383c303339e24982ec
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 965.92
# best_prompt_performance: 967.29
# best_rel_error_pct: 0.141834
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_064127.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 298.85776377272464  # OPT_PARAM: {"initial": 298.85776377272464, "min": 280, "max": 340, "type": "float"}
    safety_stock = 18.143309527662858  # OPT_PARAM: {"initial": 18.143309527662858, "min": 15, "max": 30, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.15  # OPT_PARAM: {"initial": 0.15, "min": 0.05, "max": 0.3, "type": "float"}
    adjustment_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected lead time demand
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Calculate order amount
    order_needed = target_position - net_inventory

    # Apply adjustment factor
    order_amount = max(0, order_needed * adjustment_factor)

    # Round to nearest integer
    return order_amount
