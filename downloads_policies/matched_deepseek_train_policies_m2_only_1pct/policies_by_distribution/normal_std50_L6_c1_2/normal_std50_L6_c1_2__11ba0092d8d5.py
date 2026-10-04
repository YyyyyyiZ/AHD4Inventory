# policy_hash: 11ba0092d8d57b63eb8b385adc0ee29ceb78489a0ab60693b89c013a726870d9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 4520.37
# best_prompt_performance: 4518.46
# best_rel_error_pct: 0.042253
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_230056.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 596.0760402363588  # OPT_PARAM: {"initial": 596.0760402363588, "min": 400, "max": 700, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 150, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}
    demand_buffer = 1.153043728572373  # OPT_PARAM: {"initial": 1.153043728572373, "min": 1.0, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate base order using base-stock policy with demand buffer
    base_order = max(0, base_stock * demand_buffer - inventory_position)

    # Calculate expected shortfall based on pipeline variability
    if len(pipeline_orders) > 0:
        # Consider only the most recent orders for responsiveness
        recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
        avg_recent = sum(recent_orders) / len(recent_orders)

        # Adjust order based on pipeline trend with smoother adjustment
        if avg_recent > 0:
            pipeline_ratio = pipeline_orders[-1] / avg_recent if avg_recent > 0 else 1.0
            # Smoother adjustment curve
            pipeline_adjustment = 1.0 + (pipeline_ratio - 1.0) * pipeline_weight
            pipeline_adjustment = max(0.5, min(2.0, pipeline_adjustment))
        else:
            pipeline_adjustment = 1.0
    else:
        pipeline_adjustment = 1.0

    # Calculate safety stock adjustment - only when critically low
    if on_hand_inventory < safety_stock * 0.5:
        safety_adjustment = max(0, safety_stock - on_hand_inventory) * 0.3
    else:
        safety_adjustment = 0

    # Combine adjustments with more emphasis on base order
    adjusted_order = base_order * pipeline_adjustment * adjustment_factor + safety_adjustment

    # Ensure minimum order size when inventory is very low
    if on_hand_inventory < safety_stock and adjusted_order < 50:
        adjusted_order = 50

    # Round to nearest integer (as order amount should be integer)
    order_amount = int(round(adjusted_order))

    return order_amount
