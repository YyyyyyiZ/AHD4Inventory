# policy_hash: cae3992477c28ea57c5916de18d7c445fb4623109cca4f6ab9bdff11cec1bf42
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 104
# source_prompt_files: 1
# best_target_performance: 713.37
# best_prompt_performance: 713.37
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_035629.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 562.5608024813222  # OPT_PARAM: {"initial": 562.5608024813222, "min": 400, "max": 700, "type": "float"}
    safety_stock = 27.660802481325092  # OPT_PARAM: {"initial": 27.660802481325092, "min": 0, "max": 50, "type": "float"}
    demand_forecast = 119.60418421596613  # OPT_PARAM: {"initial": 119.60418421596613, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    order_multiplier = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate inventory position with full pipeline consideration
    total_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + total_pipeline

    # Target inventory position
    target_position = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply smoothing based on forecast
    if order_amount > 0:
        order_amount = min(order_amount, demand_forecast * order_multiplier)

    return order_amount
