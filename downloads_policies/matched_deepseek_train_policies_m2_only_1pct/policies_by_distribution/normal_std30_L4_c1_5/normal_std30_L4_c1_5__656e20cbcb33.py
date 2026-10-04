# policy_hash: 656e20cbcb33f47aa7115def31f6e142058e66097be630f24050da43964608bb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_5
# matched_train_cells: 39
# source_prompt_files: 1
# best_target_performance: 3556.73
# best_prompt_performance: 3556.73
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_060630.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 460.30493081616527  # OPT_PARAM: {"initial": 460.30493081616527, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_multiplier = 0.8055264086455932  # OPT_PARAM: {"initial": 0.8055264086455932, "min": 0.5, "max": 2.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock + demand_multiplier * avg_recent_demand

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base, safety_stock * 4)

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Apply smoothing to avoid extreme orders
    max_order = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 100, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
