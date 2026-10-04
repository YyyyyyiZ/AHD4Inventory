# policy_hash: 000365806d4f04bf94c75d7054fb132084620674139dd8c964ad1ecc0940a9b6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 8407.34
# best_prompt_performance: 8406.7
# best_rel_error_pct: 0.007612
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_181410.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 614.0732881288255  # OPT_PARAM: {"initial": 614.0732881288255, "min": 300, "max": 800, "type": "float"}
    safety_stock = 99.56360733762101  # OPT_PARAM: {"initial": 99.56360733762101, "min": 0, "max": 150, "type": "float"}
    demand_forecast_factor = 0.47092298404935834  # OPT_PARAM: {"initial": 0.47092298404935834, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_weight = 0.4779062268733232  # OPT_PARAM: {"initial": 0.4779062268733232, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate demand forecast using weighted average of recent pipeline arrivals
    # More weight on most recent arrivals
    if len(pipeline_orders) >= 3:
        weights = [0.5, 0.3, 0.2]  # Decreasing weights for older orders
        weighted_sum = sum(w * d for w, d in zip(weights, pipeline_orders[:3]))
        recent_demand_estimate = weighted_sum / sum(weights[:len(pipeline_orders[:3])])
    else:
        recent_demand_estimate = base_stock / 6

    # Adjust base stock based on demand forecast
    # Use smaller adjustment factor to avoid overreacting
    adjusted_base_stock = base_stock + demand_forecast_factor * (recent_demand_estimate - base_stock / 6)

    # Calculate target inventory position with pipeline consideration
    # Reduce target when pipeline is large to avoid over-ordering
    pipeline_total = sum(pipeline_orders)
    pipeline_adjustment = pipeline_weight * (pipeline_total / len(pipeline_orders) if pipeline_orders else 0)

    target_inventory_position = adjusted_base_stock + safety_stock - pipeline_adjustment

    # Calculate order amount with smoother adjustment
    order_amount = max(0, target_inventory_position - inventory_position)

    # Apply rounding to integer
    return order_amount
