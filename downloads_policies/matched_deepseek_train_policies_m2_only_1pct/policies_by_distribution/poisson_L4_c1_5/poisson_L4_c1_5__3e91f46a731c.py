# policy_hash: 3e91f46a731c11968352aa3927a6441cf1b2c014511066c171906780b27eebf8
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 2103.44
# best_prompt_performance: 2105.08
# best_rel_error_pct: 0.077968
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044533.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 532.6365278629276  # OPT_PARAM: {"initial": 532.6365278629276, "min": 300, "max": 600, "type": "float"}
    safety_stock = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 20, "max": 120, "type": "float"}
    smoothing_factor = 0.7459116564244842  # OPT_PARAM: {"initial": 0.7459116564244842, "min": 0.5, "max": 1.0, "type": "float"}
    lead_time = 4

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time (using historical average)
    avg_demand = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}
    demand_std = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 5, "max": 20, "type": "float"}

    # Dynamic safety stock based on demand variability
    dynamic_safety = 2.9840434427314784  # OPT_PARAM: {"initial": 2.9840434427314784, "min": 0.5, "max": 3.0, "type": "float"}

    # Calculate target inventory level
    target_inventory = base_stock + dynamic_safety

    # Calculate order quantity
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing with threshold
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
