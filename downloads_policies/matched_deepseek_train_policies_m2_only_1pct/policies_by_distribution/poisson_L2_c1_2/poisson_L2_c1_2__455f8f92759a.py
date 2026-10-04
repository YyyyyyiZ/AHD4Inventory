# policy_hash: 455f8f92759ad1a435ccbd3652b168f35c3ceb1bd492f7143c8e0d613432766c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 2338.34
# best_prompt_performance: 2338.34
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_222940.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 294.0000013139217  # OPT_PARAM: {"initial": 294.0000013139217, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 78.39999999996087  # OPT_PARAM: {"initial": 78.39999999996087, "min": 50, "max": 150, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Adjust base stock based on safety stock and expected demand
    adjusted_base_stock = base_stock + safety_stock - expected_lead_time_demand

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing to reduce volatility
    smoothing_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    smoothed_order = smoothing_factor * raw_order

    # Round to nearest integer (orders must be integer quantities)
    order_amount = int(round(smoothed_order))

    return order_amount
