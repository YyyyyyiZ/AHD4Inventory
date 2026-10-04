# policy_hash: 5b7e8a1f0032adff4e43308922bb073a41e19caaf907ffa49e46753825689374
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 28
# source_prompt_files: 1
# best_target_performance: 967.64
# best_prompt_performance: 967.34
# best_rel_error_pct: 0.031003
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_234714.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 484.1643666615404  # OPT_PARAM: {"initial": 484.1643666615404, "min": 300, "max": 700, "type": "float"}
    safety_stock = 34.1643666615402  # OPT_PARAM: {"initial": 34.1643666615402, "min": 10, "max": 80, "type": "float"}
    demand_forecast = 98.1331073236353  # OPT_PARAM: {"initial": 98.1331073236353, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.5945281939772994  # OPT_PARAM: {"initial": 0.5945281939772994, "min": 0.5, "max": 1.2, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level with pipeline adjustment
    pipeline_adjustment = pipeline_weight * pipeline_orders[-1]
    target_inventory = base_stock + safety_stock - pipeline_adjustment

    # Calculate order-up-to quantity
    order_needed = target_inventory - inventory_position

    # Apply smoothing to avoid extreme order fluctuations
    if order_needed > 0:
        smoothed_order = smoothing_factor * order_needed + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Ensure non-negative order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
