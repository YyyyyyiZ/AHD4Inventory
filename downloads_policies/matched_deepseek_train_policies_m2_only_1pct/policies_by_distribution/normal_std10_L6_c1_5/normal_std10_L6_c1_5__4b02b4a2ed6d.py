# policy_hash: 4b02b4a2ed6d1e1a24b00ce4a3660476fb0d0d697e9650ecbbda092ccd91aa22
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1245.03
# best_prompt_performance: 1245.05
# best_rel_error_pct: 0.001606
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_013155.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 863.0256534736457  # OPT_PARAM: {"initial": 863.0256534736457, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 83.3369578440392  # OPT_PARAM: {"initial": 83.3369578440392, "min": 50, "max": 120, "type": "float"}
    demand_forecast = 106.23563904396616  # OPT_PARAM: {"initial": 106.23563904396616, "min": 90, "max": 110, "type": "float"}
    adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.7, "max": 1.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.6, "max": 1.0, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    reorder_point = 486.44683216761877  # OPT_PARAM: {"initial": 486.44683216761877, "min": 400, "max": 700, "type": "float"}
    max_order = 101.07442674933  # OPT_PARAM: {"initial": 101.07442674933, "min": 100, "max": 200, "type": "float"}
    min_order = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 20, "max": 80, "type": "float"}
    demand_weight = 0.7  # OPT_PARAM: {"initial": 0.7, "min": 0.3, "max": 0.7, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Blend base_stock and target_inventory based on pipeline status
    effective_base = (pipeline_weight * base_stock +
                     (1 - pipeline_weight) * target_inventory)

    # Calculate raw order amount
    raw_order = max(0, effective_base - inventory_position)

    # Apply reorder point logic: only order if inventory position is below threshold
    if inventory_position > reorder_point:
        raw_order = max(0, raw_order * 0.3)

    # Apply smoothing with demand-weighted adjustment
    smoothed_order = (smoothing_factor * raw_order +
                     (1 - smoothing_factor) * (demand_weight * demand_forecast +
                                              (1 - demand_weight) * raw_order))

    # Apply adjustment factor and cap maximum order, ensure minimum order
    order_amount = max(min_order, min(adjustment_factor * smoothed_order, max_order))

    # Round to nearest integer
    return order_amount
