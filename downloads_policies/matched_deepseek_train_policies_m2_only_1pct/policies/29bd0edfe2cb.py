# policy_hash: 29bd0edfe2cb7ca75cb8a96c8c9d6ac895280e9d8ca5f42f341fd799e4f45435
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 7279.18
# best_prompt_performance: 7249.76
# best_rel_error_pct: 0.404166
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_033727.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 304.00806386589136  # OPT_PARAM: {"initial": 304.00806386589136, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 12.024379954804706  # OPT_PARAM: {"initial": 12.024379954804706, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 81.09714051748472  # OPT_PARAM: {"initial": 81.09714051748472, "min": 10, "max": 500, "type": "float"}
    alpha = 0.01  # OPT_PARAM: {"initial": 0.01, "min": 0.01, "max": 0.99, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using exponential smoothing of recent pipeline arrivals
    # (pipeline_orders[-1] is the most recent order placed, which reflects demand from L periods ago)
    if pipeline_orders and pipeline_orders[-1] > 0:
        demand_estimate = alpha * pipeline_orders[-1] + (1 - alpha) * demand_estimate

    # Dynamic base stock adjustment based on demand estimate
    adjusted_base_stock = base_stock + safety_stock + 0.5 * demand_estimate

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
