# policy_hash: bfe23c24bd02dff9f516689cbb3b1ea2b1989bb7acb2eda220967cb8acd6d6e1
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 3028.74
# best_prompt_performance: 3024.03
# best_rel_error_pct: 0.155510
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_015246.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 457.62695205364093  # OPT_PARAM: {"initial": 457.62695205364093, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 200.0  # OPT_PARAM: {"initial": 200.0, "min": 0, "max": 200, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock * (1 + (avg_recent_demand - 100) / 1000 * demand_adjustment)

    # Calculate order amount with safety stock buffer
    order_amount = max(0, adjusted_base + safety_stock - net_inventory)

    # Round to nearest integer (since order amounts should be integers)
    return order_amount
