# policy_hash: 3ed1f108668679ac93985017b99d930e21ea1ce2c5b962d2c7cd7a782773008b
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1930.1
# best_prompt_performance: 1923.67
# best_rel_error_pct: 0.333143
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_091750.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.1445401801413  # OPT_PARAM: {"initial": 550.1445401801413, "min": 400, "max": 800, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 50, "max": 150, "type": "float"}
    demand_forecast = 85.04359263697307  # OPT_PARAM: {"initial": 85.04359263697307, "min": 80, "max": 120, "type": "float"}
    pipeline_weight = 0.7732388526240371  # OPT_PARAM: {"initial": 0.7732388526240371, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_factor = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 1.0, "type": "float"}
    lost_sales_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 2.0, "type": "float"}
    pipeline_lead_factor = 0.7196083144333062  # OPT_PARAM: {"initial": 0.7196083144333062, "min": 0.5, "max": 1.5, "type": "float"}
    demand_smoothing = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate weighted pipeline inventory with lead time consideration
    weighted_pipeline = 0
    for i, order in enumerate(pipeline_orders):
        weight = pipeline_lead_factor ** (len(pipeline_orders) - i - 1)
        weighted_pipeline += order * weight

    effective_pipeline = weighted_pipeline * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target inventory with dynamic safety stock
    target_inventory = base_stock + safety_stock * lost_sales_weight

    # Calculate deficit with smoothed demand forecast
    deficit = target_inventory - inventory_position
    smoothed_deficit = deficit * demand_smoothing + (1 - demand_smoothing) * (deficit + demand_forecast)

    # Calculate order amount with adjustment factor
    order_target = max(0, smoothed_deficit)
    order_amount = max(0, order_target * adjustment_factor)

    # Round to nearest integer
    return order_amount
