# policy_hash: 3ebfa5543ee4fa1101c806c8eb6e718e66a52f76fe3bc04ffc7adcbfbb84b63c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 12171.96
# best_prompt_performance: 12171.96
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_002848.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 446.9272413168971  # OPT_PARAM: {"initial": 446.9272413168971, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 47.92730753712278  # OPT_PARAM: {"initial": 47.92730753712278, "min": 0, "max": 200, "type": "float"}
    demand_smoothing = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[0:2]  # Last two arriving orders
    if recent_arrivals:
        avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_recent_demand = 0

    # Adjust base stock dynamically
    adjusted_base_stock = base_stock + safety_stock - demand_smoothing * avg_recent_demand

    # Calculate order amount with smoothing
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply rounding to nearest integer
    order_amount = int(round(raw_order))

    return order_amount
