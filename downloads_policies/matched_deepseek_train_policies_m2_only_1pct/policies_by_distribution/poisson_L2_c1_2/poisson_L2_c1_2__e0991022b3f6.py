# policy_hash: e0991022b3f64284864e4ba5d9fcb1bcaf5d81a23a00136501c3abc6779b59f7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 961.1
# best_prompt_performance: 960.53
# best_rel_error_pct: 0.059307
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_063040.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 305.99043856037116  # OPT_PARAM: {"initial": 305.99043856037116, "min": 250, "max": 320, "type": "float"}
    safety_stock = 22.661436917458257  # OPT_PARAM: {"initial": 22.661436917458257, "min": 5, "max": 25, "type": "float"}
    demand_estimate = 99.5  # OPT_PARAM: {"initial": 99.5, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.10582152224813965  # OPT_PARAM: {"initial": 0.10582152224813965, "min": 0.1, "max": 0.5, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}
    adjustment_factor = 0.7750772573847676  # OPT_PARAM: {"initial": 0.7750772573847676, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate weighted pipeline with exponential smoothing
    weighted_pipeline = 0
    total_weight = 0
    for i, q in enumerate(pipeline_orders):
        weight = (1 - smoothing_factor) ** i  # Exponential decay weight
        weighted_pipeline += q * weight
        total_weight += weight

    # Normalize weighted pipeline
    if total_weight > 0:
        normalized_weighted_pipeline = weighted_pipeline / total_weight
    else:
        normalized_weighted_pipeline = 0

    # Calculate target inventory position
    target_position = base_stock + safety_stock - normalized_weighted_pipeline * pipeline_weight

    # Calculate order amount with adjustment factor
    order_amount = max(0, (target_position - net_inventory) * adjustment_factor)

    # Round to nearest integer
    return order_amount
