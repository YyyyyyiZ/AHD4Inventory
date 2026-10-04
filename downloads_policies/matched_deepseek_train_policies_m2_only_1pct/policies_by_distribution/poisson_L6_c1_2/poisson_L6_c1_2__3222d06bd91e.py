# policy_hash: 3222d06bd91ea1addd957182dc845282ac13e41da3b54ec2e36e811ade947164
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 18
# source_prompt_files: 1
# best_target_performance: 1696.16
# best_prompt_performance: 1700.6
# best_rel_error_pct: 0.261768
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_161442.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 633.7288229524174  # OPT_PARAM: {"initial": 633.7288229524174, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 46.491839636453285  # OPT_PARAM: {"initial": 46.491839636453285, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 133.98894522085737  # OPT_PARAM: {"initial": 133.98894522085737, "min": 50, "max": 150, "type": "float"}
    adjustment_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected shortfall
    expected_shortfall = max(0, base_stock - inventory_position)

    # Adjust order based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / (demand_forecast * len(pipeline_orders)) if demand_forecast > 0 else 1.0
    pipeline_adjustment = 1.0 - adjustment_factor * max(0, 1.0 - pipeline_coverage)

    # Calculate final order amount
    order_amount = max(0, expected_shortfall * pipeline_adjustment + safety_stock)

    return order_amount
