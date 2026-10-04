# policy_hash: 01c489d6841a94ef36ca723fcc878039f91312590ec23002967047b8120029e3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 3223.08
# best_prompt_performance: 3234.26
# best_rel_error_pct: 0.346873
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_093842.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.0  # OPT_PARAM: {"initial": 400.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 0.0  # OPT_PARAM: {"initial": 0.0, "min": 0, "max": 150, "type": "float"}
    demand_forecast = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 80, "max": 120, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    lead_time = len(pipeline_orders)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time with safety margin
    expected_lead_time_demand = demand_forecast * lead_time

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock + expected_lead_time_demand

    # Calculate order amount with adjustment
    raw_order = max(0, target_inventory - inventory_position)
    order_amount = int(round(raw_order * adjustment_factor))

    return order_amount
