# policy_hash: f811b3eb4b62b6edafcb62edebbd15a57f902460f9349d87da5ac31a30ba4e7e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 25
# source_prompt_files: 1
# best_target_performance: 1333.36
# best_prompt_performance: 1333.36
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231733.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 277.1540815523663  # OPT_PARAM: {"initial": 277.1540815523663, "min": 200, "max": 400, "type": "float"}
    safety_stock = 57.15408155236565  # OPT_PARAM: {"initial": 57.15408155236565, "min": 0, "max": 100, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_scale = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate demand from pipeline (recent orders reflect recent demand)
    if pipeline_orders:
        recent_demand = max(pipeline_orders) * demand_scale
    else:
        recent_demand = 0

    # Adjust target based on pipeline composition
    pipeline_avg = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = pipeline_weight * (pipeline_avg - recent_demand)

    # Dynamic target
    dynamic_target = base_stock + safety_stock + recent_demand + pipeline_adjustment

    # Order amount calculation
    raw_order = max(0, dynamic_target - inventory_position)
    order_amount = int(round(adjustment_factor * raw_order))

    return order_amount
