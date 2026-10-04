# policy_hash: 9ea98c6dd12393f163000113cea965b96a0d4590d04b5cb4cf53c3633b9f7de5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 10703.74
# best_prompt_performance: 10703.74
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231013.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 342.0003652734372  # OPT_PARAM: {"initial": 342.0003652734372, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 100.1  # OPT_PARAM: {"initial": 100.1, "min": 10, "max": 500, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    pipeline_variability = max(pipeline_orders) - min(pipeline_orders) if len(pipeline_orders) > 1 else 0
    adjusted_base = base_stock + safety_stock * (pipeline_variability / 100.0)

    # Calculate order-up-to level
    order_up_to = max(adjusted_base, demand_estimate + safety_stock)

    # Place order
    order_amount = max(0, order_up_to - inventory_position)

    # Smooth ordering by considering pipeline content
    if order_amount > 0 and len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        if order_amount > 2 * avg_pipeline:
            order_amount = max(0, order_up_to - inventory_position - avg_pipeline)

    return order_amount
