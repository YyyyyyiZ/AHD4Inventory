# policy_hash: 6bf358e35215644f5b2e44d42f022ddc55569c5329f894e8e2f5de7666b30a2c
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2810.95
# best_prompt_performance: 2804.59
# best_rel_error_pct: 0.226258
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015540.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 613.4571287845533  # OPT_PARAM: {"initial": 613.4571287845533, "min": 500, "max": 700, "type": "float"}
    safety_stock = 43.45712878455295  # OPT_PARAM: {"initial": 43.45712878455295, "min": 20, "max": 80, "type": "float"}
    pipeline_factor = 0.9804502288935159  # OPT_PARAM: {"initial": 0.9804502288935159, "min": 0.8, "max": 1.1, "type": "float"}

    # Calculate effective pipeline inventory
    effective_pipeline = sum(pipeline_orders) * pipeline_factor

    # Calculate target inventory position
    target = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target - on_hand_inventory - effective_pipeline)

    # Round to nearest integer
    return order_amount
