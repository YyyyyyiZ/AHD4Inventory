# policy_hash: 5d9a4b114ccfb70fb9aca0c94074451c436d21a08649b2d7aa59e6b23e3ecbd3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 1335.44
# best_prompt_performance: 1335.58
# best_rel_error_pct: 0.010483
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_232224.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 297.74481655953997  # OPT_PARAM: {"initial": 297.74481655953997, "min": 200, "max": 350, "type": "float"}
    safety_stock = 52.74481655954268  # OPT_PARAM: {"initial": 52.74481655954268, "min": 20, "max": 80, "type": "float"}
    adjustment_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.6, "max": 1.0, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    demand_buffer = 33.22924128622543  # OPT_PARAM: {"initial": 33.22924128622543, "min": 15, "max": 40, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted average with more weight on near arrivals)
    if pipeline_orders:
        weights = [1.0 - pipeline_weight * i for i in range(len(pipeline_orders))]
        weighted_pipeline = sum(p * w for p, w in zip(pipeline_orders, weights)) / sum(weights)
    else:
        weighted_pipeline = 0

    # Dynamic target: reduce base stock when pipeline is full
    dynamic_target = base_stock + safety_stock - pipeline_weight * weighted_pipeline

    # Add demand buffer
    target_position = dynamic_target + demand_buffer

    # Calculate order with less aggressive smoothing
    raw_order = max(0, target_position - inventory_position)
    adjusted_order = adjustment_factor * raw_order

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
