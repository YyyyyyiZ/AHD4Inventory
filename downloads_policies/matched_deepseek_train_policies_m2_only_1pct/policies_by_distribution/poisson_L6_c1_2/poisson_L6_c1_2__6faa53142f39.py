# policy_hash: 6faa53142f39d07b581c6124404cc67ee858e093f4fe214f9916d2893a9d3f38
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2552.66
# best_prompt_performance: 2550.22
# best_rel_error_pct: 0.095587
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_013854.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 666.3213908707097  # OPT_PARAM: {"initial": 666.3213908707097, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 52.33184163255581  # OPT_PARAM: {"initial": 52.33184163255581, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.5199603683222888  # OPT_PARAM: {"initial": 0.5199603683222888, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate desired order-up-to level with safety stock
    target_level = base_stock + safety_stock

    # Apply smoothing to avoid large order fluctuations
    order_amount = max(0, smoothing_factor * (target_level - net_inventory))

    # Round to nearest integer (since demand is integer)
    return order_amount
