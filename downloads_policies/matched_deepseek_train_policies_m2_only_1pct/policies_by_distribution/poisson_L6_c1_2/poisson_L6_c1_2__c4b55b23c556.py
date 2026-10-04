# policy_hash: c4b55b23c55672437a7e2d1b99fbb5267268d63e54b63ee44445ab03178f4b6d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2780.08
# best_prompt_performance: 2780.99
# best_rel_error_pct: 0.032733
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015926.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 465.69723473566984  # OPT_PARAM: {"initial": 465.69723473566984, "min": 300, "max": 550, "type": "float"}
    safety_stock = 196.89223387845178  # OPT_PARAM: {"initial": 196.89223387845178, "min": 50, "max": 250, "type": "float"}
    demand_adjustment = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 1.5, "type": "float"}
    lookback_periods = 4  # OPT_PARAM: {"initial": 4, "min": 1, "max": 6, "type": "int"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:lookback_periods] if len(pipeline_orders) >= lookback_periods else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    # Use a more moderate adjustment to avoid overreacting
    demand_deviation = (avg_recent_demand - 100) / 1000
    adjusted_base = base_stock * (1 + demand_deviation * demand_adjustment)

    # Calculate order amount with safety stock buffer
    order_amount = max(0, adjusted_base + safety_stock - net_inventory)

    # Round to nearest integer (since order amounts should be integers)
    return order_amount
