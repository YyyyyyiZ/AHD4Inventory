# policy_hash: c4402dc9c1f93809b4435daaa3f1ea22a847f5332984a8e24cd4ffa6e339541f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L4_c1_5
# matched_train_cells: 12
# source_prompt_files: 1
# best_target_performance: 11451.82
# best_prompt_performance: 11451.82
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_084906.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 549.2000000002294  # OPT_PARAM: {"initial": 549.2000000002294, "min": 300, "max": 800, "type": "float"}
    safety_stock = 79.60000000010545  # OPT_PARAM: {"initial": 79.60000000010545, "min": 30, "max": 150, "type": "float"}
    demand_forecast = 119.60000000010545  # OPT_PARAM: {"initial": 119.60000000010545, "min": 80, "max": 200, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    pipeline_weight = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate weighted pipeline consideration
    weighted_pipeline = sum(p * (1 - pipeline_weight)**i for i, p in enumerate(pipeline_orders))

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + weighted_pipeline

    # Calculate target inventory
    target_inventory = demand_forecast + safety_stock

    # Calculate order amount with dual adjustment
    base_order = max(0, base_stock - inventory_position)
    target_order = max(0, target_inventory - effective_inventory)

    # Blend orders with adjustment factor
    blended_order = adjustment_factor * base_order + (1 - adjustment_factor) * target_order

    # Apply smoothing and round to integer
    order_amount = int(round(blended_order))

    return order_amount
