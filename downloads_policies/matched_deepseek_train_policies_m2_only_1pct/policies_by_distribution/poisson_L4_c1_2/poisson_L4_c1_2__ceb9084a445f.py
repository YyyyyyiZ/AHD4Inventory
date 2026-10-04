# policy_hash: ceb9084a445fcc0967620365339adcf740b633628d5b32927a55434c598b263b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 824.8
# best_prompt_performance: 824.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075031.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.4863745846346  # OPT_PARAM: {"initial": 450.4863745846346, "min": 300, "max": 600, "type": "float"}
    safety_stock = 25.48637458463469  # OPT_PARAM: {"initial": 25.48637458463469, "min": 10, "max": 60, "type": "float"}
    demand_forecast = 94.63301642264474  # OPT_PARAM: {"initial": 94.63301642264474, "min": 80, "max": 120, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base-stock policy with smoothing
    raw_order = max(0, base_stock + safety_stock - inventory_position)

    # Apply smoothing to avoid large order fluctuations
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
