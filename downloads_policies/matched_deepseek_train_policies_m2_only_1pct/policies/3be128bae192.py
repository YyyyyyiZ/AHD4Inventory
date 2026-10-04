# policy_hash: 3be128bae192b9d9ec1614f72a0f00e0861cc4f2b4d8abbf25d674de862c8e16
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 4657.77
# best_prompt_performance: 4648.47
# best_rel_error_pct: 0.199666
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_121714.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 714.824325676466  # OPT_PARAM: {"initial": 714.824325676466, "min": 600, "max": 850, "type": "float"}
    safety_stock = 174.59927056955277  # OPT_PARAM: {"initial": 174.59927056955277, "min": 120, "max": 220, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.15161860601635557  # OPT_PARAM: {"initial": 0.15161860601635557, "min": 0.05, "max": 0.25, "type": "float"}
    pipeline_weight = 0.5229814194597918  # OPT_PARAM: {"initial": 0.5229814194597918, "min": 0.3, "max": 0.7, "type": "float"}
    lost_sales_penalty_factor = 1.2906992234203092  # OPT_PARAM: {"initial": 1.2906992234203092, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline (more weight to near-term arrivals)
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Adjust base stock based on pipeline and demand forecast
    pipeline_ratio = weighted_pipeline / (base_stock + 1e-6)
    adjusted_base = base_stock * (1 + demand_forecast_factor * (1 - pipeline_ratio))

    # Calculate desired order-up-to level with lost sales penalty adjustment
    desired_level = adjusted_base + safety_stock * lost_sales_penalty_factor

    # Calculate order amount with smoothing
    raw_order = desired_level - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)

    # Round to nearest integer
    return order_amount
