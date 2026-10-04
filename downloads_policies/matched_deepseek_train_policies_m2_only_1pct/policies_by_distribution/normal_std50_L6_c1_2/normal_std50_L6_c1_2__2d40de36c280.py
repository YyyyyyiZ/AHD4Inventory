# policy_hash: 2d40de36c2805b16fc8ab6015157708d45e833a4e3276b0c4a341f35200f74a9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 4098.02
# best_prompt_performance: 4097.94
# best_rel_error_pct: 0.001952
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251217_004712.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 403.2061434301392  # OPT_PARAM: {"initial": 403.2061434301392, "min": 350, "max": 500, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 50, "type": "float"}
    demand_forecast = 90.0  # OPT_PARAM: {"initial": 90.0, "min": 90, "max": 130, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.0, "type": "float"}
    order_smoothing = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.8, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate effective inventory position with weighted pipeline
    effective_inventory = on_hand_inventory + pipeline_weight * sum(pipeline_orders)

    # Adjust base stock based on cost ratio to favor higher inventory
    adjusted_base_stock = base_stock * lost_sales_weight

    # Calculate target inventory level
    target_inventory = adjusted_base_stock + safety_stock

    # Calculate base order amount
    base_order = max(0, target_inventory - effective_inventory + demand_forecast)

    # Apply smoothing to reduce order volatility
    smoothed_order = order_smoothing * base_order + (1 - order_smoothing) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
