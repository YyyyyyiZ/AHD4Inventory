# policy_hash: 232fbddbc77460706992cc18e9fcfa4715013ac78b5517b97e315fdc450eb80e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2674.41
# best_prompt_performance: 2693.26
# best_rel_error_pct: 0.704828
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260128_100252.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 600.0  # OPT_PARAM: {"initial": 600.0, "min": 400, "max": 800, "type": "float"}
    safety_stock = 145.2267485296044  # OPT_PARAM: {"initial": 145.2267485296044, "min": 50, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time (using historical average)
    avg_demand = 104.04879508334271  # OPT_PARAM: {"initial": 104.04879508334271, "min": 80, "max": 120, "type": "float"}
    lead_time_demand = avg_demand * len(pipeline_orders)

    # Dynamic base stock level based on pipeline status
    pipeline_ratio = sum(pipeline_orders) / (len(pipeline_orders) * avg_demand) if avg_demand > 0 else 1.0
    adjusted_base = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate order-up-to level
    order_up_to = max(adjusted_base, lead_time_demand + safety_stock)

    # Calculate order amount with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    smoothing_factor = 0.777466332573862  # OPT_PARAM: {"initial": 0.777466332573862, "min": 0.3, "max": 1.0, "type": "float"}
    smoothed_order = smoothing_factor * raw_order

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
