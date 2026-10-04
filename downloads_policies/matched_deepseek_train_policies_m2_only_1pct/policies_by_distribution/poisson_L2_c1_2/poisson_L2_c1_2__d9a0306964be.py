# policy_hash: d9a0306964bef719df872ca928bf374ade46d923cefd1e886780614ff2e37826
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 1020.44
# best_prompt_performance: 1020.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_100831.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 247.27095527988826  # OPT_PARAM: {"initial": 247.27095527988826, "min": 200, "max": 350, "type": "float"}
    safety_stock = 18.405715237511075  # OPT_PARAM: {"initial": 18.405715237511075, "min": 10, "max": 50, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    demand_forecast = 95.253055359325  # OPT_PARAM: {"initial": 95.253055359325, "min": 80, "max": 120, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic base stock adjustment based on pipeline status
    if pipeline_orders[0] > demand_forecast * 1.1:  # Large incoming order
        adjusted_base_stock = base_stock - 15.0
    elif pipeline_orders[0] < demand_forecast * 0.9:  # Small incoming order
        adjusted_base_stock = base_stock + 10.0
    else:
        adjusted_base_stock = base_stock

    # Add safety stock
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    if order_amount > demand_forecast * 1.5:
        order_amount = demand_forecast * 1.5
    elif order_amount < 0:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
