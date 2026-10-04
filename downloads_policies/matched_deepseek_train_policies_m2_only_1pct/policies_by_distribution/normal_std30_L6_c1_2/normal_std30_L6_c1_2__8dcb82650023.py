# policy_hash: 8dcb82650023a0f2d4381d17b9a4455ec9e496be26be628e982ecb304f3d22f3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2668.44
# best_prompt_performance: 2682.08
# best_rel_error_pct: 0.511160
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_024144.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 589.4167925189912  # OPT_PARAM: {"initial": 589.4167925189912, "min": 400, "max": 800, "type": "float"}
    safety_stock = 149.9  # OPT_PARAM: {"initial": 149.9, "min": 20, "max": 150, "type": "float"}
    demand_forecast_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    smoothing_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lost_sales_weight = 3.0  # OPT_PARAM: {"initial": 3.0, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with lost-sales adjustment
    # Higher lost_sales_weight increases target when lost sales are more costly
    target_inventory = base_stock + safety_stock * lost_sales_weight

    # Adjust target based on pipeline status
    avg_pipeline = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_adjustment = pipeline_weight * avg_pipeline
    adjusted_target = target_inventory - pipeline_adjustment

    # Calculate base order
    base_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = base_order * smoothing_factor

    # Apply demand forecast factor
    order_amount = int(round(smoothed_order * demand_forecast_factor))

    return order_amount
