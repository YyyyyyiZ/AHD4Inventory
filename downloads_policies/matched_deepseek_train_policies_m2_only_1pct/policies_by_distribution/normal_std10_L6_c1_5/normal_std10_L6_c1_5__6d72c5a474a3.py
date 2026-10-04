# policy_hash: 6d72c5a474a379d99f7d75d7f3dfde8d6b94a1fa26146f655344965eeef578f4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1455.82
# best_prompt_performance: 1454.28
# best_rel_error_pct: 0.105782
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_205732.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 556.4858593880681  # OPT_PARAM: {"initial": 556.4858593880681, "min": 550, "max": 700, "type": "float"}
    safety_stock = 17.16204271713992  # OPT_PARAM: {"initial": 17.16204271713992, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 95.75726352089815  # OPT_PARAM: {"initial": 95.75726352089815, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.9705256998593714  # OPT_PARAM: {"initial": 0.9705256998593714, "min": 0.5, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.0203488719088667  # OPT_PARAM: {"initial": 1.0203488719088667, "min": 1.0, "max": 1.5, "type": "float"}
    pipeline_lead_factor = 0.8927848299274479  # OPT_PARAM: {"initial": 0.8927848299274479, "min": 0.7, "max": 1.0, "type": "float"}

    # Calculate weighted pipeline with lead time adjustment
    # Give more weight to near-term arrivals
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
