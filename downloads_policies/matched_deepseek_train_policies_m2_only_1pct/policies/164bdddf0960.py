# policy_hash: 164bdddf096001bb878a4239c31c87b06378be00e0d87736bb953b2442a75dde
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 2543.04
# best_prompt_performance: 2546.44
# best_rel_error_pct: 0.133698
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r8/prompt_for_code/m2_20260130_104358.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 693.000272399625  # OPT_PARAM: {"initial": 693.000272399625, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.0  # OPT_PARAM: {"initial": 50.0, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_forecast * len(pipeline_orders)

    # Calculate target inventory level with safety stock
    target_inventory = expected_lead_time_demand + safety_stock

    # Calculate order-up-to level
    order_up_to = max(base_stock, target_inventory)

    # Calculate order quantity with smoothing
    raw_order = max(0, order_up_to - inventory_position)
    order_amount = int(smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast)

    return order_amount
