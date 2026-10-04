# policy_hash: efa1ab6a5d2bbdc16493b6494ee1b15e9935b9ba24a6cc03f19c2f08f53b5c48
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 4235.51
# best_prompt_performance: 4235.51
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_024045.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 594.9189518067562  # OPT_PARAM: {"initial": 594.9189518067562, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 53.53999999998445  # OPT_PARAM: {"initial": 53.53999999998445, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 117.69999999999628  # OPT_PARAM: {"initial": 117.69999999999628, "min": 50, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_estimate * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Calculate order amount
    order_amount = max(0, target_position - inventory_position)

    # Also consider base stock as upper bound
    base_stock_order = max(0, base_stock - inventory_position)

    # Take the minimum of both approaches to avoid over-ordering
    order_amount = min(order_amount, base_stock_order)

    return order_amount
