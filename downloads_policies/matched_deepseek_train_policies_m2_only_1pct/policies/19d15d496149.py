# policy_hash: 19d15d496149d3b43dee126957bf2d8de03a31a8f89597b7fc3f6b58fda3aafc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 23
# source_prompt_files: 1
# best_target_performance: 3111.0
# best_prompt_performance: 3108.32
# best_rel_error_pct: 0.086146
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_065242.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 619.4730982657954  # OPT_PARAM: {"initial": 619.4730982657954, "min": 400, "max": 900, "type": "float"}
    safety_stock = 49.47309826578685  # OPT_PARAM: {"initial": 49.47309826578685, "min": 20, "max": 200, "type": "float"}
    pipeline_weight = 0.7327846601184881  # OPT_PARAM: {"initial": 0.7327846601184881, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate order-up-to level with safety stock adjustment
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme orders
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    if order_amount > 0:
        order_amount = order_amount * smoothing_factor

    # Round to nearest integer (as required by output type)
    order_amount = int(round(order_amount))

    return order_amount
