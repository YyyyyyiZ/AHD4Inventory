# policy_hash: 251b2f8709cf33db6063a3bcbff06ddea00e976acfe9c84e95d54d6a893b0418
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 52
# source_prompt_files: 1
# best_target_performance: 10796.21
# best_prompt_performance: 10796.21
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031609.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 264.96562500001636  # OPT_PARAM: {"initial": 264.96562500001636, "min": 100, "max": 500, "type": "float"}
    safety_stock = 59.96562499998049  # OPT_PARAM: {"initial": 59.96562499998049, "min": 20, "max": 150, "type": "float"}
    pipeline_weight_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline: give more weight to imminent arrivals
    weighted_pipeline = 0
    total_weight = 0
    for i, qty in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)  # Higher weight for earlier arrivals
        weighted_pipeline += qty * weight
        total_weight += weight

    effective_pipeline = weighted_pipeline / max(1, total_weight)

    # Adjust target based on pipeline concentration
    # If pipeline is concentrated in near future, we can lower target slightly
    pipeline_concentration = effective_pipeline / max(1, sum(pipeline_orders)) if sum(pipeline_orders) > 0 else 1.0
    adjustment = 1.0 - pipeline_weight_factor * (1.0 - pipeline_concentration)
    adjusted_base_stock = base_stock * adjustment

    # Calculate order amount
    target_inventory = adjusted_base_stock + safety_stock
    order_amount = max(0, target_inventory - inventory_position)

    # Apply integer rounding
    return order_amount
