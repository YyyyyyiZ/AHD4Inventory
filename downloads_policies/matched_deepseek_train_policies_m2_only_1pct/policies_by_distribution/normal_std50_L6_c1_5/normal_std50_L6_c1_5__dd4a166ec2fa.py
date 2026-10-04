# policy_hash: dd4a166ec2fae9d844b5fc50342659dde1c15fe1707564d49e4dda4c3cbcb24a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 50
# source_prompt_files: 1
# best_target_performance: 8538.13
# best_prompt_performance: 8538.01
# best_rel_error_pct: 0.001405
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_181035.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 614.9135863412308  # OPT_PARAM: {"initial": 614.9135863412308, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 65.90094034071353  # OPT_PARAM: {"initial": 65.90094034071353, "min": 0, "max": 300, "type": "float"}
    demand_forecast_factor = 0.2788337489333904  # OPT_PARAM: {"initial": 0.2788337489333904, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast based on recent pipeline arrivals
    # Use average of last 3 arriving orders as demand estimate
    if len(pipeline_orders) >= 3:
        recent_demand_estimate = sum(pipeline_orders[:3]) / 3
    else:
        recent_demand_estimate = base_stock / 6

    # Adjust base stock based on demand forecast
    adjusted_base_stock = base_stock + demand_forecast_factor * (recent_demand_estimate - base_stock / 6)

    # Add safety stock
    target_inventory_position = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory_position - inventory_position)

    # Round to nearest integer (as required by output type)
    return order_amount
