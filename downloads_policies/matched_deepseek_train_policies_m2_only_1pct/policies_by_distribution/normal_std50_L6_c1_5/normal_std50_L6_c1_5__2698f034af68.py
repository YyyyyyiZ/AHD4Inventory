# policy_hash: 2698f034af68c8165280d3f90bad23faade64bb6b349b70c10171440161d4801
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 6669.18
# best_prompt_performance: 6669.18
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_090917.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 776.581789559302  # OPT_PARAM: {"initial": 776.581789559302, "min": 700, "max": 1000, "type": "float"}
    safety_stock = 125.62734911652178  # OPT_PARAM: {"initial": 125.62734911652178, "min": 100, "max": 250, "type": "float"}
    demand_forecast = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 90, "max": 130, "type": "float"}
    lead_time_days = 6  # OPT_PARAM: {"initial": 6, "min": 4, "max": 8, "type": "int"}
    smoothing_factor = 0.24104485006413967  # OPT_PARAM: {"initial": 0.24104485006413967, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_quantity = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 0, "max": 50, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    # Base stock covers expected demand during lead time, safety stock for variability
    target_inventory = base_stock + safety_stock

    # Calculate raw order quantity
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    if raw_order > 0:
        order_amount = max(min_order_quantity, raw_order * smoothing_factor)
    else:
        order_amount = 0

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
