# policy_hash: f07f34cf9e6c6b29d6cab3d7cef601c8628e5f83f741485d82713ee73d02b58c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 27
# source_prompt_files: 1
# best_target_performance: 2265.2
# best_prompt_performance: 2265.2
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_055310.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 359.8563489587333  # OPT_PARAM: {"initial": 359.8563489587333, "min": 300, "max": 550, "type": "float"}
    safety_stock = 65.0  # OPT_PARAM: {"initial": 65.0, "min": 40, "max": 100, "type": "float"}
    demand_forecast = 85.1  # OPT_PARAM: {"initial": 85.1, "min": 85, "max": 115, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.9, "type": "float"}

    # Calculate inventory position with weighted pipeline
    weighted_pipeline = sum(p * (pipeline_weight ** i)
                           for i, p in enumerate(reversed(pipeline_orders)))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Dynamic safety stock based on pipeline variability
    pipeline_std = (sum((p - demand_forecast) ** 2 for p in pipeline_orders)
                    / max(1, len(pipeline_orders))) ** 0.5
    adjusted_safety = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.1, "max": 0.5, "type": "float"}

    # Calculate target inventory level
    target_inventory = expected_lead_time_demand + adjusted_safety

    # Apply base_stock cap
    order_up_to = min(base_stock, target_inventory)

    # Calculate order amount with threshold
    raw_order = max(0, order_up_to - inventory_position)

    # Apply smoothing only for significant orders
    if raw_order > demand_forecast * 0.5:  # OPT_PARAM: {"initial": 0.5, "min": 0.3, "max": 0.8, "type": "float"}
        order_amount = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast
    else:
        order_amount = raw_order

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
