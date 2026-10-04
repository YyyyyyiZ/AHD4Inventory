# policy_hash: 9eed27713a6b906de09a4c636bc346c2c8c2f5a5dcd8a7c30e8b56f71035c18b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 2183.79
# best_prompt_performance: 2183.79
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003312.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 475.1480036838496  # OPT_PARAM: {"initial": 475.1480036838496, "min": 300, "max": 800, "type": "float"}
    safety_stock = 27.847853058121647  # OPT_PARAM: {"initial": 27.847853058121647, "min": 0, "max": 150, "type": "float"}
    demand_forecast = 105.07144096016552  # OPT_PARAM: {"initial": 105.07144096016552, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0.0, "max": 0.5, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.0, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Weighted pipeline consideration - give more weight to imminent arrivals
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))

    # Adjust base stock based on recent demand pattern and pipeline status
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    adjusted_base = base_stock + safety_stock - smoothing_factor * (demand_forecast - recent_arrivals)

    # Calculate order amount with pipeline consideration
    order_amount = max(0, adjusted_base - on_hand_inventory - weighted_pipeline)

    # Round to nearest integer since order amounts should be integers
    return order_amount
