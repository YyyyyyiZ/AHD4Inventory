# policy_hash: 97a25557b23349b9191275a1254fb18e2ed1691a9b8eb77c400d694cbf7d77c1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1340.02
# best_prompt_performance: 1340.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232037.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 285.3447723611523  # OPT_PARAM: {"initial": 285.3447723611523, "min": 200, "max": 350, "type": "float"}
    safety_stock = 45.34477236115349  # OPT_PARAM: {"initial": 45.34477236115349, "min": 20, "max": 80, "type": "float"}
    adjustment_factor = 0.6460087035149713  # OPT_PARAM: {"initial": 0.6460087035149713, "min": 0.6, "max": 1.0, "type": "float"}
    pipeline_weight = 0.10000000000000003  # OPT_PARAM: {"initial": 0.10000000000000003, "min": 0.1, "max": 0.5, "type": "float"}
    demand_buffer = 28.745942099724935  # OPT_PARAM: {"initial": 28.745942099724935, "min": 15, "max": 40, "type": "float"}
    lost_sales_weight = 1.3808080387742663  # OPT_PARAM: {"initial": 1.3808080387742663, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted average with more weight on near arrivals)
    effective_pipeline = 0
    total_weight = 0
    for i, order in enumerate(pipeline_orders):
        weight = 1.0 - pipeline_weight * i
        effective_pipeline += order * weight
        total_weight += weight
    effective_pipeline = effective_pipeline / total_weight if total_weight > 0 else 0

    # Dynamic target that adjusts based on pipeline status
    # Higher pipeline_weight reduces target when pipeline is full
    dynamic_target = base_stock + safety_stock - pipeline_weight * effective_pipeline

    # Adjust for demand variability with lost-sales emphasis
    # Lost sales are more costly (p=5 vs h=1), so we prioritize avoiding them
    target_position = dynamic_target + demand_buffer * lost_sales_weight

    # Calculate order with smoother adjustment
    raw_order = max(0, target_position - inventory_position)
    adjusted_order = adjustment_factor * raw_order

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
