# policy_hash: 1e12d2e5c3389bff923dcff5563b2052bd2e230b4500d84efc79830f5ddd66a8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 3273.66
# best_prompt_performance: 3275.94
# best_rel_error_pct: 0.069647
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093939.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 411.0000000075754  # OPT_PARAM: {"initial": 411.0000000075754, "min": 300, "max": 600, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.3, "max": 1.0, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight ** i for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock + expected_lead_time_demand

    # Calculate order amount with adjustment
    raw_order = max(0, target_inventory - inventory_position)
    adjusted_order = raw_order * adjustment_factor

    # Apply minimum order quantity
    order_amount = max(min_order, int(round(adjusted_order)))

    return order_amount
