# policy_hash: b613ad322eb748e8042d227933e9aa4f146c4f4099ed9762f944f842f27bf93c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2557.65
# best_prompt_performance: 2557.64
# best_rel_error_pct: 0.000391
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081239.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 480.28061742254937  # OPT_PARAM: {"initial": 480.28061742254937, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 27.281807110212643  # OPT_PARAM: {"initial": 27.281807110212643, "min": 0, "max": 200, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    if len(pipeline_orders) > 0:
        # Use average of recent pipeline orders as demand proxy
        recent_orders = pipeline_orders[-min(3, len(pipeline_orders)):]
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = 100.0  # Default estimate

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock + (avg_recent_demand - 100) * demand_adjustment

    # Calculate target inventory position
    target_position = adjusted_base + safety_stock

    # Place order to reach target
    order_amount = max(0, target_position - inventory_position)

    return order_amount
