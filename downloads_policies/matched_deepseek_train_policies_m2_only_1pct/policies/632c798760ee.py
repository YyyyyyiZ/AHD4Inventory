# policy_hash: 632c798760ee57a8428337e5f8fb73cab4e67530eeaf4fc550207bb88a5aac97
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_5
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 6461.1
# best_prompt_performance: 6461.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260129_091224.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 836.6946550721582  # OPT_PARAM: {"initial": 836.6946550721582, "min": 700, "max": 1200, "type": "float"}
    safety_stock = 166.79465507215434  # OPT_PARAM: {"initial": 166.79465507215434, "min": 100, "max": 300, "type": "float"}
    demand_forecast = 115.0  # OPT_PARAM: {"initial": 115.0, "min": 90, "max": 140, "type": "float"}
    lead_time_days = 6  # OPT_PARAM: {"initial": 6, "min": 4, "max": 8, "type": "int"}
    smoothing_factor = 0.18774771690508973  # OPT_PARAM: {"initial": 0.18774771690508973, "min": 0.1, "max": 0.8, "type": "float"}
    min_order_quantity = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 50, "type": "float"}
    max_order_quantity = 250.0  # OPT_PARAM: {"initial": 250.0, "min": 100, "max": 400, "type": "float"}

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

    # Cap maximum order size to prevent overordering
    order_amount = min(order_amount, max_order_quantity)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
