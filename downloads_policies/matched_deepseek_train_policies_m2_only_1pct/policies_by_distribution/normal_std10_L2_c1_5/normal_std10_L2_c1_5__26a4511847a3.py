# policy_hash: 26a4511847a3fecb9bfcabfad5c1551893eeb12b4b19b5bbeec5a6311a5b3a99
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 40
# source_prompt_files: 1
# best_target_performance: 1308.2
# best_prompt_performance: 1308.82
# best_rel_error_pct: 0.047393
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_090720.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 313.8505302337036  # OPT_PARAM: {"initial": 313.8505302337036, "min": 200, "max": 350, "type": "float"}
    safety_stock = 38.17588565717394  # OPT_PARAM: {"initial": 38.17588565717394, "min": 10, "max": 50, "type": "float"}
    demand_smoothing = 0.85  # OPT_PARAM: {"initial": 0.85, "min": 0.5, "max": 1.0, "type": "float"}
    order_smoothing = 0.3256104366052445  # OPT_PARAM: {"initial": 0.3256104366052445, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand using weighted average of recent pipeline arrivals
    # More weight to most recent arrival
    if len(pipeline_orders) >= 2:
        if pipeline_orders[0] > 0 and pipeline_orders[1] > 0:
            # Weighted average: recent arrival gets more weight
            estimated_demand = (pipeline_orders[0] * 0.6 + pipeline_orders[1] * 0.4) * demand_smoothing
        elif pipeline_orders[0] > 0:
            estimated_demand = pipeline_orders[0] * demand_smoothing
        else:
            estimated_demand = 100.0  # default when no recent data
    else:
        estimated_demand = 100.0

    # Calculate order-up-to level
    # Base stock adjusted by safety stock and lead time coverage
    order_up_to = base_stock + safety_stock

    # Calculate raw order amount
    raw_order = max(0, order_up_to - net_inventory)

    # Apply smoothing based on estimated demand
    # Avoid ordering more than estimated demand for next L+1 periods
    max_reasonable_order = 3.3906170616986078  # OPT_PARAM: {"initial": 3.3906170616986078, "min": 1.5, "max": 4.0, "type": "float"}

    if raw_order > max_reasonable_order:
        order_amount = max_reasonable_order * order_smoothing + raw_order * (1 - order_smoothing)
    else:
        order_amount = raw_order

    # Round to nearest integer (orders must be integer)
    return order_amount
