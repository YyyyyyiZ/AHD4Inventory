# policy_hash: 2587b310811a1a3dc076a785e03aa25789e908649c7829ef42ad4f537bc4cbcf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 5894.3
# best_prompt_performance: 5894.3
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_030419.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 148.51999152475142  # OPT_PARAM: {"initial": 148.51999152475142, "min": 100, "max": 250, "type": "float"}
    safety_factor = 1.9198196513417636  # OPT_PARAM: {"initial": 1.9198196513417636, "min": 1.0, "max": 3.0, "type": "float"}
    demand_estimate = 131.9404412666313  # OPT_PARAM: {"initial": 131.9404412666313, "min": 80, "max": 200, "type": "float"}
    pipeline_weight = 0.44099066811857524  # OPT_PARAM: {"initial": 0.44099066811857524, "min": 0.1, "max": 0.8, "type": "float"}
    smoothing = 0.6166075095984205  # OPT_PARAM: {"initial": 0.6166075095984205, "min": 0.1, "max": 0.9, "type": "float"}
    demand_floor_weight = 0.75  # OPT_PARAM: {"initial": 0.75, "min": 0.1, "max": 1.0, "type": "float"}
    lost_sales_boost = 1.1793488925933453  # OPT_PARAM: {"initial": 1.1793488925933453, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time

    # Calculate safety stock with lost-sales boost
    safety_stock = safety_factor * (lead_time_demand ** 0.5) * lost_sales_boost
    target_inventory = base_stock + safety_stock

    # Adjust for pipeline with moderate weight
    pipeline_adjustment = pipeline_weight * sum(pipeline_orders)
    adjusted_target = max(target_inventory - pipeline_adjustment, lead_time_demand)

    # Calculate raw order
    raw_order = max(0, adjusted_target - inventory_position)

    # Apply smoothing with demand-based adjustment
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate

    # Ensure order covers expected demand with flexible floor
    incoming_order = pipeline_orders[0] if pipeline_orders else 0
    demand_floor = demand_floor_weight * max(0, demand_estimate - on_hand_inventory - incoming_order)
    final_order = max(smoothed_order, demand_floor)

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
