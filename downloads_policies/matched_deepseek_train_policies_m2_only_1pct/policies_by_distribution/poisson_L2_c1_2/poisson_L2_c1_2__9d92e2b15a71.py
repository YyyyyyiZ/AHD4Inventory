# policy_hash: 9d92e2b15a715a4fcbd35a649fdd48b828ac85791e184ebdeda8e575e507cb06
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 972.28
# best_prompt_performance: 972.28
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223124.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.0000013139217  # OPT_PARAM: {"initial": 294.0000013139217, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    adjustment_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = base_stock + safety_stock

    # Calculate order amount with adjustment factor
    raw_order = max(0, target_inventory - net_inventory)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
