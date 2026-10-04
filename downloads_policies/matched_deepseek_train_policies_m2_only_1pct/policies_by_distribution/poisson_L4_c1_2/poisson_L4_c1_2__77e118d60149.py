# policy_hash: 77e118d601498a549793a6e725065a5ba0c45462ff5f1f30f2e6c43c33fbcf72
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 10
# source_prompt_files: 1
# best_target_performance: 1763.38
# best_prompt_performance: 1763.37
# best_rel_error_pct: 0.000567
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_073424.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 456.33852905023423  # OPT_PARAM: {"initial": 456.33852905023423, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 24.359506972026534  # OPT_PARAM: {"initial": 24.359506972026534, "min": 0, "max": 200, "type": "float"}
    demand_estimate = 92.00728050014506  # OPT_PARAM: {"initial": 92.00728050014506, "min": 50, "max": 150, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on recent demand pattern
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    adjusted_base = base_stock + smoothing_factor * (demand_estimate - recent_arrivals)

    # Calculate order amount with safety stock buffer
    order_amount = max(0, adjusted_base + safety_stock - inventory_position)

    # Round to nearest integer (since order amounts should be integers)
    return order_amount
