# policy_hash: 45707ff502788ca030526d228e371919645eb7d2c5b6f7940d7f29ce86b3b0ad
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 3903.44
# best_prompt_performance: 3903.44
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_033505.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 508.89419652724416  # OPT_PARAM: {"initial": 508.89419652724416, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 76.91517444903484  # OPT_PARAM: {"initial": 76.91517444903484, "min": 0, "max": 200, "type": "float"}
    pipeline_coeff = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline composition
    # Give more weight to imminent arrivals
    weighted_pipeline = 0
    for i, q in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)  # Higher weight for earlier arrivals
        weighted_pipeline += q * weight
    avg_weight = sum(1.0/(i+1) for i in range(len(pipeline_orders))) / len(pipeline_orders)
    normalized_weighted = weighted_pipeline / avg_weight if avg_weight > 0 else 0

    # Dynamic adjustment: if pipeline is heavily weighted toward near future,
    # we can order slightly less
    pipeline_adjustment = pipeline_coeff * normalized_weighted

    # Calculate order amount with safety stock buffer
    target = base_stock + safety_stock - pipeline_adjustment
    order_amount = max(0, target - inventory_position)

    # Round to nearest integer (orders are discrete units)
    return order_amount
