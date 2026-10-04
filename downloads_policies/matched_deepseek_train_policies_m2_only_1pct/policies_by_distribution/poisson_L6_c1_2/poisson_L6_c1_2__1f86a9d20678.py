# policy_hash: 1f86a9d20678cc897243b486efeb0cddf9210a193233508e0c58c53915f9d1f9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 763.7
# best_prompt_performance: 763.4
# best_rel_error_pct: 0.039282
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_022942.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 520.0  # OPT_PARAM: {"initial": 520.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 81.85567811855692  # OPT_PARAM: {"initial": 81.85567811855692, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 120.0  # OPT_PARAM: {"initial": 120.0, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Order up to target, but ensure non-negative
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 96.03215493424185  # OPT_PARAM: {"initial": 96.03215493424185, "min": 80, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
