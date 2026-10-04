# policy_hash: e99c55955da027af05bac0b0c9ba12e633edc02263f128531d5b7f4810baafa7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 13169.43
# best_prompt_performance: 13167.56
# best_rel_error_pct: 0.014200
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_015728.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 553.755090833146  # OPT_PARAM: {"initial": 553.755090833146, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 149.74171870595654  # OPT_PARAM: {"initial": 149.74171870595654, "min": 0, "max": 500, "type": "float"}
    demand_forecast_factor = 0.38310353995218954  # OPT_PARAM: {"initial": 0.38310353995218954, "min": 0.1, "max": 2.0, "type": "float"}
    pipeline_cover_factor = 0.21773770023996283  # OPT_PARAM: {"initial": 0.21773770023996283, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on pipeline orders (proxy for recent demand)
    recent_pipeline_avg = sum(pipeline_orders[:3]) / 3 if len(pipeline_orders) >= 3 else sum(pipeline_orders) / max(len(pipeline_orders), 1)
    expected_demand = recent_pipeline_avg * demand_forecast_factor

    # Adjust base stock based on expected demand and safety stock
    adjusted_base_stock = base_stock * (1 + (expected_demand - base_stock/10) / base_stock)

    # Calculate pipeline coverage adjustment
    pipeline_coverage = sum(pipeline_orders) * pipeline_cover_factor

    # Calculate order amount with adjustments
    target_inventory = adjusted_base_stock + safety_stock - pipeline_coverage
    order_amount = max(0, target_inventory - inventory_position)

    # Round to nearest integer (as required by output type)
    return order_amount
