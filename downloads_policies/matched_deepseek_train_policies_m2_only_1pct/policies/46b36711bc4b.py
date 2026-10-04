# policy_hash: 46b36711bc4b75b89a7d2bfe36950e6090f074921ff9426947cd007cafcff397
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1249.37
# best_prompt_performance: 1249.37
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_065841.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 1049.5336035185574  # OPT_PARAM: {"initial": 1049.5336035185574, "min": 900, "max": 1200, "type": "float"}
    safety_multiplier = 1.4525483602911393  # OPT_PARAM: {"initial": 1.4525483602911393, "min": 0.8, "max": 1.8, "type": "float"}
    smoothing_factor = 0.0972073987704825  # OPT_PARAM: {"initial": 0.0972073987704825, "min": 0.05, "max": 0.3, "type": "float"}
    demand_estimate = 103.05239779560858  # OPT_PARAM: {"initial": 103.05239779560858, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.8435919424562534  # OPT_PARAM: {"initial": 0.8435919424562534, "min": 0.7, "max": 1.0, "type": "float"}
    flow_weight = 0.8631306601599994  # OPT_PARAM: {"initial": 0.8631306601599994, "min": 0.6, "max": 1.0, "type": "float"}
    min_order = 80  # OPT_PARAM: {"initial": 80, "min": 50, "max": 120, "type": "int"}

    # Calculate weighted pipeline inventory
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(pipeline_orders))
    inventory_position = on_hand_inventory + weighted_pipeline

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate safety stock
    safety_stock = safety_multiplier * (lead_time_demand ** 0.5)

    # Calculate target inventory position
    target_position = base_stock + safety_stock

    # Calculate base order using base-stock policy
    base_order = max(0, target_position - inventory_position)

    # Apply smoothing
    smoothed_order = smoothing_factor * base_order

    # Add base demand flow
    flow_order = demand_estimate

    # Blend smoothed order with flow order
    order_amount = max(0, flow_weight * flow_order + (1 - flow_weight) * smoothed_order)

    # Ensure minimum order quantity
    order_amount = max(min_order, order_amount)

    # Round to nearest integer
    return order_amount
