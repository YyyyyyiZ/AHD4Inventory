# policy_hash: 70d399b0fb8c6bc78360228ac3de240d568bf9a81b92e218ce0a723e71c28b08
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1087.84
# best_prompt_performance: 1087.84
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075504.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 250, "max": 400, "type": "float"}
    safety_stock = 40.0  # OPT_PARAM: {"initial": 40.0, "min": 20, "max": 80, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.3, "type": "float"}
    lead_time = 4

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = lead_time * demand_forecast

    # Dynamic target based on lead time demand and safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Ensure target doesn't exceed base_stock ceiling
    target_inventory = min(target_inventory, base_stock)

    # Calculate raw order quantity
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing with demand forecast as baseline
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
