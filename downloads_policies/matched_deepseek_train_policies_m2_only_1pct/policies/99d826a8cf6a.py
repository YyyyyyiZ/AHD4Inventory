# policy_hash: 99d826a8cf6a57f27f752224e2e77a705f334b8c5449f26662af662b4aa2f6c3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 2774.77
# best_prompt_performance: 2776.32
# best_rel_error_pct: 0.055860
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_013905.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 638.5112671148922  # OPT_PARAM: {"initial": 638.5112671148922, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.521717876731895  # OPT_PARAM: {"initial": 24.521717876731895, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 97.98268469060878  # OPT_PARAM: {"initial": 97.98268469060878, "min": 50, "max": 150, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate order-up-to level with safety stock adjustment
    order_up_to = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, order_up_to - net_inventory)

    # Add demand-based adjustment
    if net_inventory < base_stock:
        order_amount = max(order_amount, demand_estimate - pipeline_orders[-1] if pipeline_orders else demand_estimate)

    return order_amount
