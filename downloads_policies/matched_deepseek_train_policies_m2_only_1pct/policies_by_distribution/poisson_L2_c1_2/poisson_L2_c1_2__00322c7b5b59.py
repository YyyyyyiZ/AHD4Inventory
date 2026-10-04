# policy_hash: 00322c7b5b599f2f02512c42b7b38ca361f854b5d24d43c8d6668d9b3a0e9f99
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 705.04
# best_prompt_performance: 705.04
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_225852.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 310.0  # OPT_PARAM: {"initial": 310.0, "min": 280, "max": 340, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 15, "max": 40, "type": "float"}
    demand_forecast = 95.0  # OPT_PARAM: {"initial": 95.0, "min": 95, "max": 105, "type": "float"}
    lead_time_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.8, "max": 1.2, "type": "float"}
    adjustment_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate adjusted safety stock based on lead time
    adjusted_safety = safety_stock * lead_time_factor

    # Calculate target inventory position
    target_position = demand_forecast + adjusted_safety

    # Calculate base order-up-to level
    order_up_to = max(base_stock, target_position)

    # Calculate order needed
    order_needed = max(0, order_up_to - inventory_position)

    # Apply proportional adjustment to reduce overshooting
    if order_needed > demand_forecast:
        adjusted_order = demand_forecast + adjustment_factor * (order_needed - demand_forecast)
    else:
        adjusted_order = order_needed

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
