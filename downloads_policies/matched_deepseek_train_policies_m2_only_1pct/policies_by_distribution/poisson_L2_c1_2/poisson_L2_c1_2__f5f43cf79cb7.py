# policy_hash: f5f43cf79cb73303eb04209b5759a887c23a867a09328fc8cbc57ea6915f2591
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1050.6
# best_prompt_performance: 1050.6
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_061618.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 216.96666778046196  # OPT_PARAM: {"initial": 216.96666778046196, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 77.46947953184497  # OPT_PARAM: {"initial": 77.46947953184497, "min": 0, "max": 100, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate expected demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:2] if len(pipeline_orders) >= 2 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock * (1 + (avg_recent_demand - 100) * 0.001 * demand_adjustment)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Order up to adjusted base stock plus safety stock
    order_amount = max(0, adjusted_base + safety_stock - inventory_position)

    # Round to nearest integer (since demand is integer)
    return order_amount
