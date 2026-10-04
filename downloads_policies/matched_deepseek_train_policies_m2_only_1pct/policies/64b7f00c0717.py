# policy_hash: 64b7f00c0717cd8878525a4c93edc54b32357cb5eb3b09f661478c20399579bb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 908.79
# best_prompt_performance: 908.7
# best_rel_error_pct: 0.009903
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_202214.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 279.22798668790824  # OPT_PARAM: {"initial": 279.22798668790824, "min": 100, "max": 400, "type": "float"}
    safety_stock = 39.66840050664158  # OPT_PARAM: {"initial": 39.66840050664158, "min": 0, "max": 100, "type": "float"}
    adjustment_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.3, "type": "float"}
    pipeline_weight = 0.499999999984489  # OPT_PARAM: {"initial": 0.499999999984489, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base stock adjustment based on pipeline
    pipeline_sum = sum(pipeline_orders)
    if len(pipeline_orders) > 0:
        avg_pipeline = pipeline_sum / len(pipeline_orders)
        # Reduce safety stock when pipeline is high
        pipeline_adjustment = max(0, avg_pipeline - base_stock * pipeline_weight)
        adjusted_base = base_stock + safety_stock - pipeline_adjustment
    else:
        adjusted_base = base_stock + safety_stock

    # Calculate order amount
    raw_order = max(0, adjusted_base - inventory_position)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
