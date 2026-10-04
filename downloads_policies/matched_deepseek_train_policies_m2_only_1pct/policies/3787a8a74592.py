# policy_hash: 3787a8a74592fe881f646d448783ad243bc190bb25c182851889c05ccff2399b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 5359.39
# best_prompt_performance: 5358.75
# best_rel_error_pct: 0.011942
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251217_011426.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 504.12872156730106  # OPT_PARAM: {"initial": 504.12872156730106, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 20.176551425333905  # OPT_PARAM: {"initial": 20.176551425333905, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 108.92076580326265  # OPT_PARAM: {"initial": 108.92076580326265, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on recent demand pattern
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    adjusted_base = base_stock + safety_stock - smoothing_factor * (demand_forecast - recent_arrivals)

    # Calculate order amount
    order_amount = max(0, adjusted_base - inventory_position)

    # Round to nearest integer since order amounts should be integers
    return order_amount
