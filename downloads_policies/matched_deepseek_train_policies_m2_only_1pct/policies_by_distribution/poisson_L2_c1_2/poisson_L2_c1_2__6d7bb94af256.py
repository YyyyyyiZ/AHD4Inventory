# policy_hash: 6d7bb94af256956b89f8eccc77463e39a11cdf66d284b89d5cb6609e33a85242
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 17
# source_prompt_files: 1
# best_target_performance: 898.06
# best_prompt_performance: 898.06
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_224011.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 290.34079485626177  # OPT_PARAM: {"initial": 290.34079485626177, "min": 200, "max": 400, "type": "float"}
    safety_stock = 35.0  # OPT_PARAM: {"initial": 35.0, "min": 10, "max": 80, "type": "float"}
    demand_forecast = 98.56063520581642  # OPT_PARAM: {"initial": 98.56063520581642, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.25  # OPT_PARAM: {"initial": 0.25, "min": 0.0, "max": 0.3, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline variability
    if len(pipeline_orders) >= 2:
        pipeline_avg = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_variability = abs(pipeline_orders[0] - pipeline_avg) + abs(pipeline_orders[1] - pipeline_avg)
        adjustment = pipeline_weight * (demand_forecast - pipeline_variability)
    else:
        adjustment = 0

    adjusted_base = base_stock + adjustment

    # Calculate order-up-to level
    order_up_to = max(adjusted_base, demand_forecast + safety_stock)

    # Calculate order amount
    raw_order = max(0, order_up_to - inventory_position)
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
