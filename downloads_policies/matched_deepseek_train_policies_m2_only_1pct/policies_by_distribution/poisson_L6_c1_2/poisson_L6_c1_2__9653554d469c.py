# policy_hash: 9653554d469cef4e330d92feff8999bec59edb258dd4f333adda86e5158516f5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1625.1
# best_prompt_performance: 1624.06
# best_rel_error_pct: 0.063996
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_050146.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 574.5310606603956  # OPT_PARAM: {"initial": 574.5310606603956, "min": 400, "max": 700, "type": "float"}
    safety_multiplier = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 0.5, "max": 2.0, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate expected demand during lead time
    avg_demand = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}
    demand_std = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 5, "max": 20, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate safety stock based on demand variability
    safety_stock = safety_multiplier * demand_std * (lead_time ** 0.5)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer
    return order_amount
