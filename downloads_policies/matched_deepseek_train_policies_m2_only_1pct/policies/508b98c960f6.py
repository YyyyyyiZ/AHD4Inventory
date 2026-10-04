# policy_hash: 508b98c960f6a3fae0983709cbcc1f802ff7cf51a16b8a19100d9357220e6b09
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 11573.82
# best_prompt_performance: 11573.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084638.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 428.4201488863546  # OPT_PARAM: {"initial": 428.4201488863546, "min": 300, "max": 600, "type": "float"}
    safety_stock = 52.992923765598945  # OPT_PARAM: {"initial": 52.992923765598945, "min": 20, "max": 150, "type": "float"}
    demand_estimate = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 180, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.3, "max": 1.0, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * pipeline_weight**(i+1) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate target inventory level with adjustment
    target_inventory = expected_lead_time_demand + safety_stock

    # Use the maximum of base_stock and target_inventory
    order_up_to = max(base_stock, target_inventory)

    # Calculate order amount with adjustment factor
    order_amount = max(0, (order_up_to - inventory_position) * adjustment_factor)

    # Round to nearest integer
    return order_amount
