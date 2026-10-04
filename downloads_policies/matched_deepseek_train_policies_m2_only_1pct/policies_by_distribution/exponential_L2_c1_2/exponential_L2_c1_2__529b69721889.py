# policy_hash: 529b69721889043f6230f5c495f537687a93f63dbb79424e93f093dbc492c7fc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 6420.3
# best_prompt_performance: 6420.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023552.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 181.2222804310846  # OPT_PARAM: {"initial": 181.2222804310846, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 23.27592637311364  # OPT_PARAM: {"initial": 23.27592637311364, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 62.47515315607514  # OPT_PARAM: {"initial": 62.47515315607514, "min": 10, "max": 500, "type": "float"}
    adjustment_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand coverage
    expected_demand = demand_estimate * (len(pipeline_orders) + 1)

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Calculate order amount with adjustment for pipeline
    order_amount = max(0, target_position - inventory_position + adjustment_factor * (expected_demand - inventory_position))

    # Round to nearest integer (orders must be integer)
    return order_amount
