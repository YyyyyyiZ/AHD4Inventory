# policy_hash: 14842794650b6820c828f0b10424d171096aa061381fa508c5a52dd47bea42fe
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 11953.2
# best_prompt_performance: 11953.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_020043.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 562.7875397346852  # OPT_PARAM: {"initial": 562.7875397346852, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 158.8000000005668  # OPT_PARAM: {"initial": 158.8000000005668, "min": 0, "max": 300, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    demand_estimate = 108.80000000056681  # OPT_PARAM: {"initial": 108.80000000056681, "min": 50, "max": 200, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate effective pipeline (weighted sum)
    weighted_pipeline = sum(p * (pipeline_weight ** i)
                           for i, p in enumerate(pipeline_orders))

    # Calculate target inventory level
    target = base_stock + safety_stock + demand_estimate

    # Calculate order amount with adjustment
    net_inventory = on_hand_inventory + weighted_pipeline
    raw_order = max(0, target - net_inventory)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
