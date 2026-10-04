# policy_hash: 374e806a609bc634c6633e43aa80a9fada4d81e775d35c6f361f1ef18035cf37
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 6276.98
# best_prompt_performance: 6276.68
# best_rel_error_pct: 0.004779
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251218_013809.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.0  # OPT_PARAM: {"initial": 320.0, "min": 200, "max": 450, "type": "float"}
    safety_stock = 122.70005608061604  # OPT_PARAM: {"initial": 122.70005608061604, "min": 80, "max": 200, "type": "float"}
    demand_estimate = 109.9503122183919  # OPT_PARAM: {"initial": 109.9503122183919, "min": 80, "max": 150, "type": "float"}
    pipeline_weight = 0.6232888045463308  # OPT_PARAM: {"initial": 0.6232888045463308, "min": 0.5, "max": 1.0, "type": "float"}
    adjustment_smoothing = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.3, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = demand_estimate * len(pipeline_orders)

    # Calculate effective pipeline (weighted sum)
    effective_pipeline = sum(p * pipeline_weight for p in pipeline_orders)

    # Calculate target inventory level with higher safety stock
    target_level = max(base_stock, lead_time_demand + safety_stock - effective_pipeline)

    # Calculate order amount with smoothing
    raw_order = target_level - inventory_position
    order_amount = raw_order * adjustment_smoothing

    # Ensure non-negative and round to integer
    order_amount = max(0, order_amount)
    order_amount = int(round(order_amount))

    return order_amount
