# policy_hash: f4d35aaf6cb6e4d29e2645484ac0fd62bccadd1362192890da6c3771252e852c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6286.76
# best_prompt_performance: 6286.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013503.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 380.0  # OPT_PARAM: {"initial": 380.0, "min": 300, "max": 500, "type": "float"}
    safety_stock = 91.60065236600545  # OPT_PARAM: {"initial": 91.60065236600545, "min": 50, "max": 120, "type": "float"}
    demand_estimate = 109.99950002980192  # OPT_PARAM: {"initial": 109.99950002980192, "min": 90, "max": 140, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    adjustment_smoothing = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate effective pipeline (weighted sum with higher weight on near-term arrivals)
    weights = [pipeline_weight ** (len(pipeline_orders) - i - 1) for i in range(len(pipeline_orders))]
    effective_pipeline = sum(p * w for p, w in zip(pipeline_orders, weights))

    # Calculate target inventory level
    target_level = max(base_stock, lead_time_demand + safety_stock - effective_pipeline)

    # Calculate order amount with smoothing
    raw_order = target_level - inventory_position
    order_amount = raw_order * adjustment_smoothing

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
