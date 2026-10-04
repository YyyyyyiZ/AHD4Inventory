# policy_hash: 349aaec63d2457297e956849ed87cc31b1dbcd392ba2b3c367342a63258eecc0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 5891.52
# best_prompt_performance: 5891.52
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_025546.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 192.5012618671863  # OPT_PARAM: {"initial": 192.5012618671863, "min": 100, "max": 400, "type": "float"}
    safety_factor = 1.8187813684291292  # OPT_PARAM: {"initial": 1.8187813684291292, "min": 1.0, "max": 3.0, "type": "float"}
    demand_estimate = 91.61294125948793  # OPT_PARAM: {"initial": 91.61294125948793, "min": 50, "max": 300, "type": "float"}
    pipeline_weight = 0.791474480925102  # OPT_PARAM: {"initial": 0.791474480925102, "min": 0.1, "max": 0.8, "type": "float"}
    smoothing = 0.4698446939259429  # OPT_PARAM: {"initial": 0.4698446939259429, "min": 0.1, "max": 0.9, "type": "float"}
    min_order_multiplier = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time = len(pipeline_orders)
    lead_time_demand = demand_estimate * lead_time

    # Safety stock based on lead time demand variability
    safety_stock = safety_factor * (lead_time_demand ** 0.5)
    target_inventory = base_stock + safety_stock

    # Adjust for pipeline orders more aggressively
    pipeline_adjustment = pipeline_weight * sum(pipeline_orders)
    adjusted_target = max(target_inventory - pipeline_adjustment, lead_time_demand)

    # Calculate raw order
    raw_order = max(0, adjusted_target - inventory_position)

    # Apply stronger smoothing
    smoothed_order = smoothing * raw_order + (1 - smoothing) * demand_estimate

    # Minimum order based on expected demand and current coverage
    min_order = max(0, min_order_multiplier * demand_estimate - on_hand_inventory - pipeline_orders[0])
    final_order = max(smoothed_order, min_order)

    # Round to nearest integer
    order_amount = int(round(final_order))

    return order_amount
