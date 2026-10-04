# policy_hash: 61af51207a1396512f9e93ae875e4554ad432440743706a86a9d6f73c90618cf
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1224.9
# best_prompt_performance: 1224.9
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_032415.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 281.8502201629398  # OPT_PARAM: {"initial": 281.8502201629398, "min": 250, "max": 320, "type": "float"}
    safety_stock = 31.384492096718493  # OPT_PARAM: {"initial": 31.384492096718493, "min": 30, "max": 60, "type": "float"}
    demand_estimate = 95.48775604332953  # OPT_PARAM: {"initial": 95.48775604332953, "min": 95, "max": 105, "type": "float"}
    pipeline_weight = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    order_smoothing = 0.12184028345043138  # OPT_PARAM: {"initial": 0.12184028345043138, "min": 0.02, "max": 0.15, "type": "float"}
    lost_sales_weight = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 1.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple pipeline adjustment
    avg_pipeline = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    pipeline_deviation = (avg_pipeline - demand_estimate) / demand_estimate if demand_estimate > 0 else 0

    # Dynamic target: increase when pipeline is below demand
    adjusted_base = base_stock * (1 - pipeline_weight * pipeline_deviation)
    target_level = adjusted_base + safety_stock * lost_sales_weight

    # Base order amount
    base_order = max(0, target_level - inventory_position)

    # Apply smoothing with demand consideration
    smoothed_order = order_smoothing * base_order + (1 - order_smoothing) * demand_estimate

    # Ensure non-negative integer order
    order_amount = max(0, int(round(smoothed_order)))

    return order_amount
