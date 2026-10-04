# policy_hash: 911ccb9b0eabf740616171a5b8907907de0370bd183183eb2be85cf2e5ba9a42
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 7009.1
# best_prompt_performance: 7010.64
# best_rel_error_pct: 0.021971
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_035105.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 370.3030545463568  # OPT_PARAM: {"initial": 370.3030545463568, "min": 300, "max": 500, "type": "float"}
    safety_stock = 11.328289847523582  # OPT_PARAM: {"initial": 11.328289847523582, "min": 0, "max": 80, "type": "float"}
    pipeline_coeff = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 0.7, "max": 1.1, "type": "float"}
    demand_smoothing = 0.3057947015087603  # OPT_PARAM: {"initial": 0.3057947015087603, "min": 0.15, "max": 0.6, "type": "float"}
    order_rounding = 5  # OPT_PARAM: {"initial": 5, "min": 1, "max": 20, "type": "int"}

    # Calculate effective inventory position with discounted pipeline
    effective_pipeline = sum(pipeline_orders) * pipeline_coeff
    inventory_position = on_hand_inventory + effective_pipeline

    # Estimate upcoming demand from recent pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    demand_estimate = recent_arrivals * demand_smoothing

    # Adjust base stock dynamically based on demand estimate
    adjusted_base_stock = base_stock + safety_stock + demand_estimate

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Round to nearest multiple of order_rounding
    if order_rounding > 1:
        order_amount = round(order_amount / order_rounding) * order_rounding

    # Ensure integer output
    order_amount = int(order_amount)

    return order_amount
