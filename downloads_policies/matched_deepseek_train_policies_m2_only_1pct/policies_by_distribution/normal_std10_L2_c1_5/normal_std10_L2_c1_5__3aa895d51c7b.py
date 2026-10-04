# policy_hash: 3aa895d51c7b2be40517eee9a1844beffbb523f4c5543ada1de9a7ceb98ee1a2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L2_c1_5
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 1372.7
# best_prompt_performance: 1371.67
# best_rel_error_pct: 0.075035
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L2_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_094005.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 287.29205008484087  # OPT_PARAM: {"initial": 287.29205008484087, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 29.474479175124312  # OPT_PARAM: {"initial": 29.474479175124312, "min": 0, "max": 200, "type": "float"}
    pipeline_weight = 0.9766880563442484  # OPT_PARAM: {"initial": 0.9766880563442484, "min": 0.0, "max": 1.0, "type": "float"}
    demand_adjustment_factor = 0.13150320845163727  # OPT_PARAM: {"initial": 0.13150320845163727, "min": 0.0, "max": 0.5, "type": "float"}
    recent_demand_window = 5  # OPT_PARAM: {"initial": 5, "min": 1, "max": 20, "type": "int"}

    # Calculate effective inventory position
    effective_pipeline = pipeline_weight * sum(pipeline_orders)
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjust base stock based on safety stock
    adjusted_base_stock = base_stock + safety_stock

    # Calculate order amount using base stock policy
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply demand smoothing: reduce order volatility
    if order_amount > 0:
        # Reduce large orders to prevent overstocking
        smoothed_order = order_amount * (1.0 - demand_adjustment_factor)
        order_amount = max(0, smoothed_order)

    # Round to nearest integer since order amounts should be integers
    return order_amount
