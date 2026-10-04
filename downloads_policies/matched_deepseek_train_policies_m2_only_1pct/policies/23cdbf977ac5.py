# policy_hash: 23cdbf977ac5563a39e190f1ef8a90ddb158c25432e84e8def55b8511b4618d8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 4998.73
# best_prompt_performance: 5000.62
# best_rel_error_pct: 0.037810
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_002548.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 454.0278706642653  # OPT_PARAM: {"initial": 454.0278706642653, "min": 300, "max": 600, "type": "float"}
    safety_stock = 19.027870664266263  # OPT_PARAM: {"initial": 19.027870664266263, "min": 0, "max": 50, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    inventory_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 34.027870664266125  # OPT_PARAM: {"initial": 34.027870664266125, "min": 10, "max": 60, "type": "float"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(p * (pipeline_weight ** i)
                          for i, p in enumerate(pipeline_orders))

    # Calculate inventory position
    inventory_position = (inventory_weight * on_hand_inventory +
                         weighted_pipeline)

    # Adjust base stock with safety stock and demand buffer
    adjusted_base_stock = base_stock + safety_stock + demand_buffer

    # Order amount calculation
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
