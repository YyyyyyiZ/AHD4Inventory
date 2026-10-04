# policy_hash: 11317c81dd5265e6ffa62a66fb06997233c660a78459daf894cec7aa963c5dd5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2085.42
# best_prompt_performance: 2089.18
# best_rel_error_pct: 0.180299
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_044401.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 401.2073111309631  # OPT_PARAM: {"initial": 401.2073111309631, "min": 350, "max": 500, "type": "float"}
    safety_stock = 51.39614738431947  # OPT_PARAM: {"initial": 51.39614738431947, "min": 40, "max": 100, "type": "float"}
    smoothing_factor = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.7, "max": 1.0, "type": "float"}
    demand_estimate = 89.11705110775559  # OPT_PARAM: {"initial": 89.11705110775559, "min": 80, "max": 120, "type": "float"}
    lead_time_factor = 1.0130942098720008  # OPT_PARAM: {"initial": 1.0130942098720008, "min": 0.8, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * lead_time_factor

    # Dynamic target based on pipeline and expected demand
    target_inventory = base_stock + safety_stock + expected_lead_time_demand

    # Calculate order quantity
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing
    if order_amount > 0:
        order_amount = smoothing_factor * order_amount

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
