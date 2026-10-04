# policy_hash: ab6f8ab013301c7695411d05dda18ccae5c38e50a6dbe75c96908812beb893c7
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1461.74
# best_prompt_performance: 1461.74
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_024318.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 468.4167202849479  # OPT_PARAM: {"initial": 468.4167202849479, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 9.078444770340676  # OPT_PARAM: {"initial": 9.078444770340676, "min": 0, "max": 200, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock + demand_adjustment * (avg_recent_demand - 100)

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base, safety_stock + avg_recent_demand * 4)

    # Order amount
    order_amount = max(0, order_up_to - net_inventory)

    # Smooth ordering by limiting large changes
    max_order_change = 56.24415342850675  # OPT_PARAM: {"initial": 56.24415342850675, "min": 50, "max": 200, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        if abs(order_amount - last_order) > max_order_change:
            if order_amount > last_order:
                order_amount = last_order + max_order_change
            else:
                order_amount = max(0, last_order - max_order_change)

    return order_amount
