# policy_hash: 546dc0041d2ba332acc8832323868077d785d7dc0dc32b294f331c083bd08d3b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 3336.89
# best_prompt_performance: 3336.89
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015007.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 633.9430883408387  # OPT_PARAM: {"initial": 633.9430883408387, "min": 400, "max": 900, "type": "float"}
    safety_stock = 63.99643356227393  # OPT_PARAM: {"initial": 63.99643356227393, "min": 50, "max": 200, "type": "float"}
    demand_forecast = 102.5  # OPT_PARAM: {"initial": 102.5, "min": 80, "max": 120, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus one period
    expected_demand_lead_time_plus_one = demand_forecast * (lead_time + 1)

    # Calculate target inventory position
    target_inventory_position = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory_position - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
