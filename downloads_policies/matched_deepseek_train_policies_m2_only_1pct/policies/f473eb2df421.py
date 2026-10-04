# policy_hash: f473eb2df421de0865c26acb051cf051378e82eab5f03935a01b99c73aedac8b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 45
# source_prompt_files: 1
# best_target_performance: 1329.22
# best_prompt_performance: 1329.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_231347.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 304.0992472314123  # OPT_PARAM: {"initial": 304.0992472314123, "min": 200, "max": 400, "type": "float"}
    safety_stock = 40.1234369070305  # OPT_PARAM: {"initial": 40.1234369070305, "min": 0, "max": 100, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.2, "type": "float"}
    adjustment_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simpler pipeline adjustment: weight recent pipeline more heavily
    if len(pipeline_orders) > 0:
        # Weight pipeline orders (newer orders get higher weight)
        weighted_pipeline = 0
        total_weight = 0
        for i, order in enumerate(pipeline_orders):
            weight = (i + 1) * pipeline_weight  # Increasing weight for newer orders
            weighted_pipeline += order * weight
            total_weight += weight

        avg_weighted_pipeline = weighted_pipeline / total_weight if total_weight > 0 else 0
        # Adjust base stock based on weighted pipeline average
        adjusted_base = base_stock + safety_stock * (1 - avg_weighted_pipeline / base_stock)
    else:
        adjusted_base = base_stock

    # Calculate order amount with simpler adjustment
    raw_order = max(0, adjusted_base - inventory_position)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
