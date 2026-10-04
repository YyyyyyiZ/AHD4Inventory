# policy_hash: 33fd0f89a2a4fe79347050115c9020a274af700cd5e7f33ac365dad6076df4fc
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1589.86
# best_prompt_performance: 1589.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_143458.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.3370398201695  # OPT_PARAM: {"initial": 450.3370398201695, "min": 300, "max": 600, "type": "float"}
    safety_stock = 80.43703982016957  # OPT_PARAM: {"initial": 80.43703982016957, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.6080800490404269  # OPT_PARAM: {"initial": 0.6080800490404269, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Smooth adjustment to avoid large order swings
    order_amount = max(0, smoothing_factor * (target_inventory - inventory_position))

    # Round to nearest integer since order amount must be integer
    order_amount = int(round(order_amount))

    return order_amount
