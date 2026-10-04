# policy_hash: 98b70db7fa34ff678620a95f57cbf3bc350337cc27ec63a68621e87baae07ca2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 3061.14
# best_prompt_performance: 3061.14
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_013848.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 663.9895492381544  # OPT_PARAM: {"initial": 663.9895492381544, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = lead_time_demand + safety_stock

    # Order up to target, but ensure non-negative
    order_amount = max(0, target_position - net_inventory)

    # Cap large orders to avoid overordering
    max_order = 200  # OPT_PARAM: {"initial": 200, "min": 100, "max": 300, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Round to nearest integer since demand is integer
    order_amount = int(round(order_amount))

    return order_amount
