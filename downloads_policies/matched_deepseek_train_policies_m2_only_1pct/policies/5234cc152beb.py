# policy_hash: 5234cc152bebd4dff5418ca7cbef316a8ce78aa5d3cffd479281cb72eb6cf3b4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 2114.56
# best_prompt_performance: 2114.56
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_203253.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 647.57252457848  # OPT_PARAM: {"initial": 647.57252457848, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 3.799104150188516  # OPT_PARAM: {"initial": 3.799104150188516, "min": 0, "max": 200, "type": "float"}
    demand_buffer = 49.57279905486898  # OPT_PARAM: {"initial": 49.57279905486898, "min": 0, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from pipeline arrival pattern
    # Use weighted average of recent pipeline orders as demand proxy
    if len(pipeline_orders) >= 3:
        recent_weight = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.1, "max": 1.0, "type": "float"}
        older_weight = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.0, "max": 0.9, "type": "float"}

        recent_avg = sum(pipeline_orders[:3]) / 3 if len(pipeline_orders) >= 3 else 100
        older_avg = sum(pipeline_orders[3:]) / max(1, len(pipeline_orders) - 3) if len(pipeline_orders) > 3 else 100

        estimated_demand = recent_avg * recent_weight + older_avg * older_weight
    else:
        estimated_demand = 100.0

    # Dynamic base stock adjustment
    dynamic_adjustment = 0.00032705008707509785  # OPT_PARAM: {"initial": 0.00032705008707509785, "min": 0.0, "max": 2.0, "type": "float"}
    adjusted_base = base_stock + dynamic_adjustment

    # Calculate order amount with safety stock consideration
    target_inventory = adjusted_base + safety_stock + demand_buffer
    order_amount = max(0, target_inventory - inventory_position)

    # Smooth ordering to avoid large fluctuations
    max_order_increase = 41.498613131036734  # OPT_PARAM: {"initial": 41.498613131036734, "min": 10, "max": 200, "type": "float"}
    if len(pipeline_orders) > 0:
        last_order = pipeline_orders[-1]
        order_amount = min(order_amount, last_order + max_order_increase)

    return order_amount
