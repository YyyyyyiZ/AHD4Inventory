# policy_hash: 3d0967aed0ee455ab7323904947b8ab78cd95a5238f36880813af2585733128c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 12693.96
# best_prompt_performance: 12693.96
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015903.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 554.0001061912697  # OPT_PARAM: {"initial": 554.0001061912697, "min": 50, "max": 800, "type": "float"}
    pipeline_coverage = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position (on-hand + pipeline)
    total_pipeline = sum(pipeline_orders)
    inventory_position = on_hand_inventory + total_pipeline

    # Simple base-stock policy
    order_amount = max(0, base_stock - inventory_position)

    # Apply pipeline coverage adjustment
    if total_pipeline > 0:
        avg_lead_time_demand = base_stock * pipeline_coverage
        if total_pipeline > avg_lead_time_demand:
            order_amount = max(0, order_amount * 0.5)  # Reduce order if pipeline is large

    # Round to nearest integer
    return order_amount
