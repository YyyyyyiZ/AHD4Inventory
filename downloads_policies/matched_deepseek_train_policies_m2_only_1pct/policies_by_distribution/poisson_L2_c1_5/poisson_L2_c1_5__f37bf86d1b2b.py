# policy_hash: f37bf86d1b2b4126c74be8499418951694e148beda58ea2f6280a78d3a7fa3ac
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 1228.5
# best_prompt_performance: 1228.5
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031735.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 279.2440330873098  # OPT_PARAM: {"initial": 279.2440330873098, "min": 200, "max": 350, "type": "float"}
    safety_stock = 14.244033087309607  # OPT_PARAM: {"initial": 14.244033087309607, "min": 5, "max": 40, "type": "float"}
    demand_estimate = 99.0312366935151  # OPT_PARAM: {"initial": 99.0312366935151, "min": 90, "max": 110, "type": "float"}
    pipeline_weight = 0.228711261751241  # OPT_PARAM: {"initial": 0.228711261751241, "min": 0.1, "max": 0.5, "type": "float"}
    smoothing_factor = 0.11659401470457881  # OPT_PARAM: {"initial": 0.11659401470457881, "min": 0.05, "max": 0.4, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    target_level = base_stock + safety_stock

    # Base order amount
    base_order = max(0, target_level - inventory_position)

    # Add pipeline-aware adjustment
    if len(pipeline_orders) > 0:
        expected_pipeline = demand_estimate * len(pipeline_orders)
        current_pipeline = sum(pipeline_orders)
        pipeline_deficit = max(0, expected_pipeline - current_pipeline)
        base_order += pipeline_weight * pipeline_deficit

    # Apply smoothing
    order_amount = smoothing_factor * base_order + (1 - smoothing_factor) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(order_amount)))

    return order_amount
