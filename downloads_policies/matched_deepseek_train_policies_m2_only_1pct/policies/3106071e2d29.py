# policy_hash: 3106071e2d298175b5601a934cc50305ae973958c39888cbeebccb05b64b180c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 22
# source_prompt_files: 1
# best_target_performance: 816.03
# best_prompt_performance: 816.03
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_050324.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 479.0593889817447  # OPT_PARAM: {"initial": 479.0593889817447, "min": 400, "max": 600, "type": "float"}
    safety_stock = 9.059388981743291  # OPT_PARAM: {"initial": 9.059388981743291, "min": 0, "max": 50, "type": "float"}
    smoothing_factor = 0.05165258204328205  # OPT_PARAM: {"initial": 0.05165258204328205, "min": 0.0, "max": 0.5, "type": "float"}
    demand_adjustment = -5.940611018256676  # OPT_PARAM: {"initial": -5.940611018256676, "min": -20, "max": 20, "type": "float"}
    pipeline_weight = 0.13443505469552136  # OPT_PARAM: {"initial": 0.13443505469552136, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on demand adjustment parameter
    adjusted_base = base_stock + demand_adjustment

    # Calculate target inventory position
    target_inventory = adjusted_base + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with pipeline consideration
    if pipeline_orders and raw_order > 0:
        # Consider pipeline orders in smoothing
        pipeline_influence = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
        smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * pipeline_influence
        # Further adjust based on pipeline weight
        order_amount = (1 - pipeline_weight) * smoothed_order + pipeline_weight * raw_order
    else:
        order_amount = raw_order

    # Ensure integer order amount
    return order_amount
