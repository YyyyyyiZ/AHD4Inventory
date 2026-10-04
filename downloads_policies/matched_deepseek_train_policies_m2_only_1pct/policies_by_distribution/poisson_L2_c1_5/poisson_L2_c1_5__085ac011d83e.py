# policy_hash: 085ac011d83e1d9c4a90bd7990a5a314b178577bf3ac27e5607fa3cb51d59c90
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 57
# source_prompt_files: 2
# best_target_performance: 1427.26
# best_prompt_performance: 1427.26
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_230444.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.9814814814807  # OPT_PARAM: {"initial": 308.9814814814807, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    expected_lead_time_demand = demand_estimate * lead_time

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock + smoothing_factor * expected_lead_time_demand

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer since order amount must be integer
    order_amount = int(round(order_amount))

    return order_amount
