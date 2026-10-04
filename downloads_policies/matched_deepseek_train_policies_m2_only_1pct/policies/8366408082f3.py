# policy_hash: 8366408082f3668640ebf6e4b5ea6e1ea1c193c4d400871becc99275cfcd49cc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 953.62
# best_prompt_performance: 953.62
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223540.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 309.999846128059  # OPT_PARAM: {"initial": 309.999846128059, "min": 200, "max": 400, "type": "float"}
    safety_stock = 15.099846128059028  # OPT_PARAM: {"initial": 15.099846128059028, "min": 0, "max": 50, "type": "float"}
    adjustment_factor = 0.7413440885797682  # OPT_PARAM: {"initial": 0.7413440885797682, "min": 0.5, "max": 1.5, "type": "float"}
    pipeline_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate effective pipeline (weighted sum with more weight on near-term arrivals)
    weighted_pipeline = sum(pipeline_orders[i] * (pipeline_weight ** i) for i in range(len(pipeline_orders)))

    # Calculate net inventory position with weighted pipeline
    net_inventory = on_hand_inventory + weighted_pipeline

    # Dynamic safety stock based on pipeline variability
    pipeline_variability = max(pipeline_orders) - min(pipeline_orders) if len(pipeline_orders) > 1 else 0
    dynamic_safety = safety_stock + 0.1 * pipeline_variability

    # Calculate target inventory
    target_inventory = base_stock + dynamic_safety

    # Calculate order amount
    raw_order = max(0, target_inventory - net_inventory)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
