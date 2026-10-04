# policy_hash: e1600d67d26dfd84dbfea4608c7428bc87a9ebba53f0bdddf9280920f060099b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2057.08
# best_prompt_performance: 2067.63
# best_rel_error_pct: 0.512863
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_055852.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 576.9433690293223  # OPT_PARAM: {"initial": 576.9433690293223, "min": 450, "max": 650, "type": "float"}
    safety_stock = 160.0  # OPT_PARAM: {"initial": 160.0, "min": 100, "max": 160, "type": "float"}
    smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    demand_buffer = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.3, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.4, "type": "float"}
    min_order = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 60, "type": "float"}
    max_order = 150.0  # OPT_PARAM: {"initial": 150.0, "min": 150, "max": 250, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 90, "max": 110, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand using weighted pipeline average
    weighted_sum = 0.0
    weight_sum = 0.0
    for i, order in enumerate(reversed(pipeline_orders)):
        weight = pipeline_weight ** i
        weighted_sum += order * weight
        weight_sum += weight

    if weight_sum > 0 and weighted_sum > 0:
        avg_pipeline_demand = weighted_sum / weight_sum
    else:
        avg_pipeline_demand = demand_estimate

    # Dynamic target with demand buffer
    dynamic_target = base_stock + safety_stock + (demand_buffer - 1.0) * avg_pipeline_demand

    # Calculate order with smoothing
    raw_order = dynamic_target - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)

    # Apply order limits
    order_amount = max(min_order, min(max_order, order_amount))

    # Round to nearest integer
    return order_amount
