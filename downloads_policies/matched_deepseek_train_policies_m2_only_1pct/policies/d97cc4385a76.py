# policy_hash: d97cc4385a76cdcba2b6d1a1ee2e1956811d281b5f77e451bbd892ea51deb760
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 5345.32
# best_prompt_performance: 5342.72
# best_rel_error_pct: 0.048641
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_225429.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 582.379826176407  # OPT_PARAM: {"initial": 582.379826176407, "min": 400, "max": 700, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 150, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate base order using base-stock policy
    base_order = max(0, base_stock - inventory_position)

    # Calculate expected shortfall based on pipeline variability
    if len(pipeline_orders) > 0:
        # Consider only the most recent orders for responsiveness
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        avg_recent = sum(recent_orders) / len(recent_orders)

        # Adjust order based on pipeline trend
        if avg_recent > 0:
            pipeline_ratio = pipeline_orders[-1] / avg_recent if avg_recent > 0 else 1.0
            pipeline_adjustment = max(0.5, min(2.0, pipeline_ratio))
        else:
            pipeline_adjustment = 1.0
    else:
        pipeline_adjustment = 1.0

    # Calculate safety stock adjustment
    safety_adjustment = max(0, safety_stock - on_hand_inventory) * 0.5

    # Combine adjustments
    adjusted_order = base_order * pipeline_adjustment * adjustment_factor + safety_adjustment

    # Round to nearest integer (as order amount should be integer)
    order_amount = int(round(adjusted_order))

    return order_amount
