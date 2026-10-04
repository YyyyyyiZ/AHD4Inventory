# policy_hash: a862bc368c9a278a4048edc290862fcc08ea6000c5173ce71cd4309cb50c4493
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 17092.0
# best_prompt_performance: 17092.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081037.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.0  # OPT_PARAM: {"initial": 450.0, "min": 300, "max": 600, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Calculate order-up-to level
    order_up_to = max(0, target_position - inventory_position + expected_lead_time_demand)

    # Smooth ordering by considering pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / max(1, demand_estimate)
    if pipeline_coverage > 3.0:  # OPT_PARAM: {"initial": 3.0, "min": 2.0, "max": 5.0, "type": "float"}
        order_up_to = order_up_to * 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.0, "type": "float"}

    # Ensure order amount is integer and non-negative
    order_amount = max(0, int(round(order_up_to)))

    return order_amount
