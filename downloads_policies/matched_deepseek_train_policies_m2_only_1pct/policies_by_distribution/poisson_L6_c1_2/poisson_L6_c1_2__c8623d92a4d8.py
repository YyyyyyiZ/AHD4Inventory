# policy_hash: c8623d92a4d873145f9a37c8ce8dd4473901ccf5adc4d0f13773251f582c5642
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 975.29
# best_prompt_performance: 978.85
# best_rel_error_pct: 0.365020
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_085459.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 795.1342943701296  # OPT_PARAM: {"initial": 795.1342943701296, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 174.2207030049688  # OPT_PARAM: {"initial": 174.2207030049688, "min": 0, "max": 200, "type": "float"}
    demand_forecast = 124.22070300495723  # OPT_PARAM: {"initial": 124.22070300495723, "min": 50, "max": 150, "type": "float"}
    pipeline_weight = 0.15833733751318296  # OPT_PARAM: {"initial": 0.15833733751318296, "min": 0.1, "max": 1.5, "type": "float"}
    adjustment_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate effective inventory position
    effective_pipeline = sum(pipeline_orders) * pipeline_weight
    inventory_position = on_hand_inventory + effective_pipeline

    # Calculate target order
    target = base_stock + safety_stock - inventory_position

    # Add demand forecast adjustment
    target += demand_forecast

    # Apply smoothing adjustment
    order_amount = max(0, target * adjustment_factor)

    # Round to nearest integer
    return order_amount
