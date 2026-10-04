# policy_hash: 8913999c4c5131c43770c9c74fe8eccab5263aac529c6a9b7a3db5f76ef5f8d6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 1427.24
# best_prompt_performance: 1427.24
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230728.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 276.79999999999984  # OPT_PARAM: {"initial": 276.79999999999984, "min": 200, "max": 350, "type": "float"}
    safety_stock = 21.79999999999916  # OPT_PARAM: {"initial": 21.79999999999916, "min": 0, "max": 100, "type": "float"}
    demand_estimate = 97.60000000000034  # OPT_PARAM: {"initial": 97.60000000000034, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.11  # OPT_PARAM: {"initial": 0.11, "min": 0.01, "max": 0.2, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = demand_estimate * lead_time

    # Adjust base stock based on pipeline variability
    pipeline_variability = sum(abs(p - demand_estimate) for p in pipeline_orders) / max(1, len(pipeline_orders))
    adjusted_base = base_stock - pipeline_weight * pipeline_variability

    # Calculate target inventory level
    target_inventory = adjusted_base + safety_stock + smoothing_factor * expected_lead_time_demand

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer since order amount must be integer
    order_amount = int(round(order_amount))

    return order_amount
