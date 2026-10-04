# policy_hash: 5384fe1920ea250b6d3bfc356793d029aa2d27792132cfcee8fa6eb7b8fd23ec
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 19
# source_prompt_files: 1
# best_target_performance: 1415.74
# best_prompt_performance: 1415.5
# best_rel_error_pct: 0.016952
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_210333.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 554.964144472784  # OPT_PARAM: {"initial": 554.964144472784, "min": 550, "max": 700, "type": "float"}
    safety_stock = 15.640327801855612  # OPT_PARAM: {"initial": 15.640327801855612, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.5, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}
    pipeline_lead_factor = 0.7999999999999999  # OPT_PARAM: {"initial": 0.7999999999999999, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate weighted pipeline with lead time adjustment
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_lead_factor ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight

    weighted_pipeline *= pipeline_weight

    # Calculate inventory position
    inventory_position = on_hand_inventory + weighted_pipeline

    # Adjust base stock based on lost sales risk
    adjusted_base = base_stock * lost_sales_weight

    # Calculate order-up-to level with safety stock
    order_up_to = adjusted_base + safety_stock - inventory_position

    # Apply smoothing with demand forecast adjustment
    if order_up_to > 0:
        # Blend between order-up-to and forecasted demand
        smoothed_order = smoothing_factor * order_up_to + (1 - smoothing_factor) * demand_forecast
    else:
        smoothed_order = 0

    # Round to nearest integer and ensure non-negative
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
