# policy_hash: 717cef5680328d77cc7a21eb6f60349b4683e2217ac0516dc6e815839de42af3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 3579.42
# best_prompt_performance: 3587.02
# best_rel_error_pct: 0.212325
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_053536.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 569.2139264968037  # OPT_PARAM: {"initial": 569.2139264968037, "min": 400, "max": 800, "type": "float"}
    safety_stock = 89.31392649679509  # OPT_PARAM: {"initial": 89.31392649679509, "min": 50, "max": 200, "type": "float"}
    pipeline_coverage = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.3, "type": "float"}

    # Calculate expected demand based on recent pipeline arrivals
    # Use average of pipeline orders as proxy for recent demand pattern
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        expected_demand = avg_pipeline * demand_buffer
    else:
        expected_demand = 100.0  # Default estimate

    # Calculate effective inventory position with pipeline coverage
    effective_pipeline = sum(pipeline_orders) * pipeline_coverage
    inventory_position = on_hand_inventory + effective_pipeline

    # Dynamic target level based on expected demand and safety stock
    dynamic_target = base_stock + safety_stock + expected_demand * 0.5

    # Calculate order amount
    order_amount = max(0, dynamic_target - inventory_position)

    # Apply smoothing: don't order tiny amounts
    if order_amount < expected_demand * 0.3:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
