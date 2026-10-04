# policy_hash: 9ded9ca7bd74fff8fe09e501f9047d7446bf97ba96c6c16a42b956f0c5ce4219
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 3969.12
# best_prompt_performance: 3969.82
# best_rel_error_pct: 0.017636
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_020609.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 507.44226603318805  # OPT_PARAM: {"initial": 507.44226603318805, "min": 300, "max": 700, "type": "float"}
    safety_stock = 142.44234292463625  # OPT_PARAM: {"initial": 142.44234292463625, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lead_time = 4

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time (using historical average)
    avg_demand = 95.05424047904482  # OPT_PARAM: {"initial": 95.05424047904482, "min": 80, "max": 120, "type": "float"}
    demand_std = 36.343309046165984  # OPT_PARAM: {"initial": 36.343309046165984, "min": 20, "max": 50, "type": "float"}

    # Dynamic safety stock based on demand variability
    dynamic_safety = safety_stock * (1 + demand_std / avg_demand)

    # Calculate target level with dynamic safety stock
    target_level = base_stock + dynamic_safety

    # Calculate raw order amount
    raw_order = max(0, target_level - inventory_position)

    # Apply smoothing with minimum order threshold
    min_order_threshold = 20.1  # OPT_PARAM: {"initial": 20.1, "min": 10, "max": 50, "type": "float"}

    if raw_order > min_order_threshold:
        order_amount = int(round(smoothing_factor * raw_order))
    else:
        order_amount = 0

    return order_amount
