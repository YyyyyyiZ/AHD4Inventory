# policy_hash: 8e896bcde0437a67d05cd638a069fccb79d32f48d5a43cb3f99903813f76677a
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1425.3
# best_prompt_performance: 1425.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035601.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 286.9656326563054  # OPT_PARAM: {"initial": 286.9656326563054, "min": 250, "max": 350, "type": "float"}
    safety_stock = 13.96563265630585  # OPT_PARAM: {"initial": 13.96563265630585, "min": 0, "max": 30, "type": "float"}
    demand_forecast = 104.93346806627957  # OPT_PARAM: {"initial": 104.93346806627957, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.3, "max": 0.7, "type": "float"}
    threshold_factor = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position with dynamic adjustment
    target_position = base_stock + safety_stock + expected_demand_during_leadtime

    # Calculate order gap
    order_gap = target_position - inventory_position

    # Apply threshold-based ordering: only order if gap is significant
    if order_gap > threshold_factor * demand_forecast:
        # Smooth ordering with ceiling to ensure integer orders
        order_amount = max(0, int(smoothing_factor * order_gap + 0.5))
    else:
        order_amount = 0

    return order_amount
