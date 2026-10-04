# policy_hash: aa255bbb930dd278dfbca30e9a94829899e670ace4ef0fe5d6213593996997a3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1749.8
# best_prompt_performance: 1749.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073611.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 481.9745352043345  # OPT_PARAM: {"initial": 481.9745352043345, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 49.99344138910922  # OPT_PARAM: {"initial": 49.99344138910922, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 87.94177018914158  # OPT_PARAM: {"initial": 87.94177018914158, "min": 50, "max": 150, "type": "float"}
    pipeline_weight = 0.9648766186999151  # OPT_PARAM: {"initial": 0.9648766186999151, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on demand forecast
    adjusted_base = base_stock * (demand_forecast / 100.0)

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Round to nearest integer (since order amount must be integer)
    order_amount = int(round(order_amount))

    return order_amount
