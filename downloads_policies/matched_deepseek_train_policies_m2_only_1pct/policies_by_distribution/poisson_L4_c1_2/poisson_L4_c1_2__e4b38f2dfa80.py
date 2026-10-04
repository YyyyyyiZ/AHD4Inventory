# policy_hash: e4b38f2dfa80e287fc37ff1cfdd01d1e2fcc3a3165c68fcbd300f8acd7d973c5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1358.54
# best_prompt_performance: 1358.54
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_074052.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 514.1616846684011  # OPT_PARAM: {"initial": 514.1616846684011, "min": 400, "max": 600, "type": "float"}
    safety_stock = 74.15633341663195  # OPT_PARAM: {"initial": 74.15633341663195, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position with weighted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Use smoothed demand forecast adjustment
    adjusted_base = base_stock * (demand_forecast / 100.0)

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base + safety_stock

    # Smooth order quantity to reduce volatility
    desired_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * desired_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
