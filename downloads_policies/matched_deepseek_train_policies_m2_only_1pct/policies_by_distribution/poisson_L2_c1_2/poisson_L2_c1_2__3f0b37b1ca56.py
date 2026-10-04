# policy_hash: 3f0b37b1ca568152cfad28be01b0d55940bc552236901d96366aa61b99e21fa9
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 1342.38
# best_prompt_performance: 1342.38
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_021831.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 297.80000131392137  # OPT_PARAM: {"initial": 297.80000131392137, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 28.80000000000047  # OPT_PARAM: {"initial": 28.80000000000047, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    estimated_demand = recent_arrivals * demand_adjustment

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on safety stock and estimated demand
    adjusted_base_stock = base_stock + safety_stock - estimated_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - net_inventory)

    # Round to nearest integer (since order amount should be integer)
    order_amount = int(round(order_amount))

    return order_amount
