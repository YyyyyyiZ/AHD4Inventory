# policy_hash: 7ddbc73172b7d713f8a2e02cee93a12a110d838f25de3688debb3d5440dceca0
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 2638.88
# best_prompt_performance: 2638.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_074401.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 712.2487850377348  # OPT_PARAM: {"initial": 712.2487850377348, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 14.138250928674553  # OPT_PARAM: {"initial": 14.138250928674553, "min": 0, "max": 200, "type": "float"}
    demand_adjustment_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline orders
    recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_order = sum(recent_orders) / max(len(recent_orders), 1)

    # Adjust base stock based on recent demand pattern
    adjusted_base_stock = base_stock + (avg_recent_order * demand_adjustment_factor - 100) * 2.0

    # Calculate order amount with safety stock consideration
    target_inventory = max(adjusted_base_stock, base_stock - safety_stock)
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering by limiting large changes
    max_order_change = 174.52124893990643  # OPT_PARAM: {"initial": 174.52124893990643, "min": 50, "max": 300, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        if abs(order_amount - last_order) > max_order_change:
            if order_amount > last_order:
                order_amount = last_order + max_order_change
            else:
                order_amount = max(0, last_order - max_order_change)

    return order_amount
