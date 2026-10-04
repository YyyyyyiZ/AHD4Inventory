# policy_hash: a6648b26a6d883dd03324ef3fe4773de3119aa6a1dee5c23a6ba0d7f14606a04
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 5895.98
# best_prompt_performance: 5895.98
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025049.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 159.03767779371472  # OPT_PARAM: {"initial": 159.03767779371472, "min": 100, "max": 400, "type": "float"}
    safety_stock = 19.037677793716057  # OPT_PARAM: {"initial": 19.037677793716057, "min": 10, "max": 100, "type": "float"}
    demand_estimate = 89.06953255579766  # OPT_PARAM: {"initial": 89.06953255579766, "min": 50, "max": 200, "type": "float"}
    smoothing = 0.44756369223491943  # OPT_PARAM: {"initial": 0.44756369223491943, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time

    # Calculate order-up-to level with safety stock
    order_up_to = base_stock + safety_stock

    # Ensure order-up-to covers at least lead time demand
    order_up_to = max(order_up_to, lead_time_demand)

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
