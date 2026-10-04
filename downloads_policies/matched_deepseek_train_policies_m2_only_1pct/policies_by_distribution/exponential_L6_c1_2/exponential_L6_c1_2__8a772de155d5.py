# policy_hash: 8a772de155d551c338b4fdbaf05cdccca4ddcab22773f9d38ed07a14555500e6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 6142.96
# best_prompt_performance: 6142.96
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_014654.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.0  # OPT_PARAM: {"initial": 420.0, "min": 350, "max": 550, "type": "float"}
    safety_stock = 171.22567430123192  # OPT_PARAM: {"initial": 171.22567430123192, "min": 120, "max": 250, "type": "float"}
    demand_estimate = 107.70694545964238  # OPT_PARAM: {"initial": 107.70694545964238, "min": 100, "max": 150, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_smoothing = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate effective pipeline (weighted sum)
    effective_pipeline = sum(p * pipeline_weight for p in pipeline_orders)

    # Adjust safety stock based on lost-sales cost ratio
    adjusted_safety_stock = safety_stock * lost_sales_weight

    # Calculate target inventory level
    target_level = max(base_stock, lead_time_demand + adjusted_safety_stock - effective_pipeline)

    # Calculate order amount with smoothing
    raw_order = target_level - inventory_position
    order_amount = raw_order * adjustment_smoothing

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
