# policy_hash: 807d6a98da764612d540a00984479a295279e4cbcd54219d7ba7075521d41ac1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 3411.08
# best_prompt_performance: 3408.12
# best_rel_error_pct: 0.086776
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093445.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 20, "max": 150, "type": "float"}
    demand_forecast = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}
    reorder_threshold = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 10, "max": 100, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock + expected_lead_time_demand

    # Calculate order amount with adjustment
    raw_order = max(0, target_inventory - inventory_position)

    # Apply reorder threshold - only order if needed
    if raw_order < reorder_threshold:
        order_amount = 0
    else:
        order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
