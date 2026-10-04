# policy_hash: 77b9cc19a9a3f94abf48a713f086e0ea26ed15696d641ea1ef32c1a6d6558463
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 31
# source_prompt_files: 2
# best_target_performance: 1035.5
# best_prompt_performance: 1035.5
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_100311.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 273.8024320708377  # OPT_PARAM: {"initial": 273.8024320708377, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.19748453163266  # OPT_PARAM: {"initial": 20.19748453163266, "min": 0, "max": 150, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on pipeline orders (as proxy for recent demand)
    # Use average of recent pipeline arrivals as demand estimate
    if len(pipeline_orders) > 0:
        recent_demand_estimate = sum(pipeline_orders) / len(pipeline_orders)
    else:
        recent_demand_estimate = 100.0  # Default estimate

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock * (1 + smoothing_factor * (recent_demand_estimate - 100) / 100)

    # Add safety stock
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer (since demand is integer)
    return order_amount
