# policy_hash: 5d9445255968442644900053c26dbe6f44c3e9763298c55010343c7a45b0f2af
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1859.9
# best_prompt_performance: 1873.68
# best_rel_error_pct: 0.740900
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260129_214204.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 611.3438714403115  # OPT_PARAM: {"initial": 611.3438714403115, "min": 600, "max": 900, "type": "float"}
    safety_stock = 50.22963322110788  # OPT_PARAM: {"initial": 50.22963322110788, "min": 50, "max": 120, "type": "float"}
    adjustment_factor = 0.6169058944049247  # OPT_PARAM: {"initial": 0.6169058944049247, "min": 0.6, "max": 1.0, "type": "float"}
    lead_time = 6

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Use more accurate demand estimate
    avg_demand = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 110, "type": "float"}

    # Calculate pipeline coverage with exponential weights
    pipeline_coverage = 0.0
    total_weight = 0.0
    for i, q in enumerate(pipeline_orders):
        weight = 2.0 ** (len(pipeline_orders) - i - 1)  # Exponential weights: 32,16,8,4,2,1
        pipeline_coverage += q * weight
        total_weight += weight

    # Normalize pipeline coverage
    if total_weight > 0:
        pipeline_coverage = pipeline_coverage / total_weight * len(pipeline_orders)

    # Dynamic safety stock adjustment
    if len(pipeline_orders) > 0:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_std = (sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / len(pipeline_orders)) ** 0.5
        volatility_factor = 0.2677971194221088  # OPT_PARAM: {"initial": 0.2677971194221088, "min": 0.1, "max": 0.5, "type": "float"}
        safety_adjustment = volatility_factor * pipeline_std
    else:
        safety_adjustment = 0.0

    # Calculate target inventory with lead time consideration
    lead_time_factor = 1.0196801338862658  # OPT_PARAM: {"initial": 1.0196801338862658, "min": 1.0, "max": 1.5, "type": "float"}
    target = base_stock + safety_stock + safety_adjustment + lead_time_factor * avg_demand

    # Order amount calculation
    order_amount = max(0, target - inventory_position)

    # Apply adjustment factor
    order_amount = adjustment_factor * order_amount

    # Cap order amount based on demand variability
    max_order_multiplier = 1.5  # OPT_PARAM: {"initial": 1.5, "min": 1.5, "max": 3.5, "type": "float"}
    order_cap = max_order_multiplier * avg_demand

    # Round to nearest integer and apply cap
    order_amount = min(int(round(order_amount)), order_cap)

    return order_amount
