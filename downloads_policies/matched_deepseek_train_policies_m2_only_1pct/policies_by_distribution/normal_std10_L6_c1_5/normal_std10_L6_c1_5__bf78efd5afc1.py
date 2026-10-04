# policy_hash: bf78efd5afc1d547931054ff980df23d3214540c31ff7b3cf4b86912eed88605
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1821.06
# best_prompt_performance: 1832.26
# best_rel_error_pct: 0.615026
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_202335.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 649.5188250826884  # OPT_PARAM: {"initial": 649.5188250826884, "min": 500, "max": 800, "type": "float"}
    safety_stock = 14.527192953086745  # OPT_PARAM: {"initial": 14.527192953086745, "min": 0, "max": 50, "type": "float"}
    demand_forecast = 99.11799375937721  # OPT_PARAM: {"initial": 99.11799375937721, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock - inventory_position

    # Apply smoothing
    if order_up_to > 0:
        smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
