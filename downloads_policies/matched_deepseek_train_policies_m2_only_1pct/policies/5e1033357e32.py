# policy_hash: 5e1033357e3241bd1879c04347bb2d4b2ae3f0799dc1d39e5352de57c23c678d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 11
# source_prompt_files: 1
# best_target_performance: 1285.74
# best_prompt_performance: 1285.5
# best_rel_error_pct: 0.018666
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_004842.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.92461903619244  # OPT_PARAM: {"initial": 450.92461903619244, "min": 450, "max": 520, "type": "float"}
    safety_stock = 30.17389773388419  # OPT_PARAM: {"initial": 30.17389773388419, "min": 30, "max": 60, "type": "float"}
    demand_forecast = 95.09422234359376  # OPT_PARAM: {"initial": 95.09422234359376, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}

    # Calculate effective inventory position with discounted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Dynamic order-up-to level based on forecast and safety stock
    order_up_to = base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, order_up_to - inventory_position)

    # Apply stronger smoothing toward demand forecast
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = max(0, int(smoothed_order + 0.5))

    return order_amount
