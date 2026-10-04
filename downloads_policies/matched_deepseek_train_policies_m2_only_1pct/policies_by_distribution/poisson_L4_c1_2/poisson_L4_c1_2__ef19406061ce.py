# policy_hash: ef19406061cec901d09336e61222eec35b9aa5bdd151fa06385ceccddc6dae1e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1572.98
# best_prompt_performance: 1572.98
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035727.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 461.62033170036847  # OPT_PARAM: {"initial": 461.62033170036847, "min": 350, "max": 500, "type": "float"}
    safety_stock = 80.0  # OPT_PARAM: {"initial": 80.0, "min": 20, "max": 80, "type": "float"}
    smoothing_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.5, "max": 1.0, "type": "float"}
    lead_time = 4  # Fixed lead time

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time (using historical average)
    avg_demand = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 80, "max": 120, "type": "float"}
    demand_variability = 15.0  # OPT_PARAM: {"initial": 15.0, "min": 5, "max": 30, "type": "float"}

    # Dynamic desired level based on pipeline composition
    pipeline_imbalance = abs(pipeline_orders[0] - avg_demand) if pipeline_orders else 0
    adjustment = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}

    desired_level = base_stock + safety_stock - adjustment

    # Calculate order amount with smoothing
    raw_order = desired_level - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)

    # Round to nearest integer
    return order_amount
