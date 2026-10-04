# policy_hash: 15f100199041211d9a39d73c015581541853012e645fd5a0f17225465bc164a4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 72
# source_prompt_files: 2
# best_target_performance: 949.52
# best_prompt_performance: 949.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_023252.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 200, "max": 500, "type": "float"}
    safety_stock = 180.00278519269628  # OPT_PARAM: {"initial": 180.00278519269628, "min": 100, "max": 250, "type": "float"}
    demand_estimate = 100.00253629463272  # OPT_PARAM: {"initial": 100.00253629463272, "min": 80, "max": 120, "type": "float"}
    lead_time_factor = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.0, "max": 1.5, "type": "float"}
    adjustment_factor = 0.703902287530377  # OPT_PARAM: {"initial": 0.703902287530377, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with adjustment factor
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders) * lead_time_factor

    # Calculate target inventory level
    target_inventory = expected_demand_during_leadtime + safety_stock

    # Calculate order amount with smoothing
    order_amount = max(0, target_inventory - net_inventory)

    # Apply adjustment factor to smooth ordering
    order_amount = order_amount * adjustment_factor

    # Apply base stock as upper bound
    order_amount = min(order_amount, max(0, base_stock - net_inventory))

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
