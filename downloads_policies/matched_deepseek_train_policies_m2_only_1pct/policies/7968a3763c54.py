# policy_hash: 7968a3763c54445401a29b96ed32ee8b866fe3583ce02a48fc869efca7d6b0bd
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 10739.42
# best_prompt_performance: 10739.42
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031904.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 200, "max": 450, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 30, "max": 100, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple demand forecast using only the most recent pipeline arrival
    if pipeline_orders:
        # Use the most recent arrival as demand indicator (q_{t,1} arrived this period)
        recent_demand_indicator = pipeline_orders[0]
    else:
        recent_demand_indicator = 0

    # Adjust base stock level based on recent demand
    demand_adjustment = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.2, "type": "float"}
    adjusted_base_stock = base_stock + safety_stock + demand_adjustment

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - inventory_position)

    # Apply order smoothing with simpler approach
    max_order = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 100, "max": 300, "type": "float"}
    order_amount = min(order_amount, max_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
