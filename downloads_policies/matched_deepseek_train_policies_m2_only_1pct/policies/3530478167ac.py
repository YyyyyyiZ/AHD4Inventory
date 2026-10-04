# policy_hash: 3530478167ac00bb96415badacf4615bca89df05bd106204afb35a0d22a58c27
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 10213.1
# best_prompt_performance: 10213.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073605.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 269.20000000000226  # OPT_PARAM: {"initial": 269.20000000000226, "min": 100, "max": 500, "type": "float"}
    safety_stock = 69.40000000000404  # OPT_PARAM: {"initial": 69.40000000000404, "min": 20, "max": 150, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 0.8, "type": "float"}
    demand_estimate = 94.40000000000404  # OPT_PARAM: {"initial": 94.40000000000404, "min": 50, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate effective pipeline (weighted average with more weight on near arrivals)
    weighted_pipeline = 0
    total_weight = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_weight ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight
        total_weight += weight

    effective_pipeline = weighted_pipeline / (total_weight + 1e-6)

    # Adjust base stock based on pipeline composition
    pipeline_ratio = effective_pipeline / (sum(pipeline_orders) + 1e-6)
    adjusted_base = base_stock * (0.8 + 0.4 * pipeline_ratio)

    # Calculate target inventory
    target_inventory = adjusted_base + safety_stock * (demand_estimate / 100)

    # Calculate order amount
    order_needed = target_inventory - inventory_position
    order_amount = max(0, order_needed * adjustment_factor)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
