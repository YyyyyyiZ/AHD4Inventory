# policy_hash: e2eefe560b0ac2143972da1311a02551ae78953beb220999dfbd15ace76fcc03
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 1506.22
# best_prompt_performance: 1506.22
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_003209.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 449.23119249924247  # OPT_PARAM: {"initial": 449.23119249924247, "min": 300, "max": 600, "type": "float"}
    safety_stock = 49.23119249924241  # OPT_PARAM: {"initial": 49.23119249924241, "min": 0, "max": 150, "type": "float"}
    demand_forecast = 96.80751233291836  # OPT_PARAM: {"initial": 96.80751233291836, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level
    order_up_to = base_stock + safety_stock

    # Simple order-up-to policy
    raw_order = max(0, order_up_to - inventory_position)

    # Smooth ordering
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
