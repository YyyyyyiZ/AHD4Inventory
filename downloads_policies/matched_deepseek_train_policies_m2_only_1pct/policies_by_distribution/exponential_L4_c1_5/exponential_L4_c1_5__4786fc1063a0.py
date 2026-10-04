# policy_hash: 4786fc1063a098e006e88dcbf9acd93f8ce69f6dbb483afbd1f12c40905cb656
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 26
# source_prompt_files: 1
# best_target_performance: 10999.68
# best_prompt_performance: 10999.68
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_090013.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 480.6895637069555  # OPT_PARAM: {"initial": 480.6895637069555, "min": 300, "max": 700, "type": "float"}
    pipeline_weight = 0.8320426117980555  # OPT_PARAM: {"initial": 0.8320426117980555, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.23922556707883327  # OPT_PARAM: {"initial": 0.23922556707883327, "min": 0.1, "max": 0.4, "type": "float"}
    safety_stock = 120.68956370695568  # OPT_PARAM: {"initial": 120.68956370695568, "min": 50, "max": 250, "type": "float"}
    demand_anticipation = 0.23922556707883327  # OPT_PARAM: {"initial": 0.23922556707883327, "min": 0.0, "max": 0.3, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjusted base stock with safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order-up-to amount
    order_up_to = max(0, adjusted_base_stock - inventory_position)

    # Apply demand anticipation based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / adjusted_base_stock if adjusted_base_stock > 0 else 1.0
    if pipeline_coverage < 0.4:
        order_up_to *= (1 + demand_anticipation)

    # Apply smoothing
    order_amount = smoothing_factor * order_up_to

    # Ensure integer order amount
    order_amount = int(round(order_amount))

    return order_amount
