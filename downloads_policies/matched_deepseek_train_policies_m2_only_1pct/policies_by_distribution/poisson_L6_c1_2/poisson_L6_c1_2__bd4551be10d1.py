# policy_hash: bd4551be10d1871f63b989b05490a34e62fad99c9b50d732c99ec7a5a43edaee
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 2949.42
# best_prompt_performance: 2949.42
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_021813.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 568.4423125928977  # OPT_PARAM: {"initial": 568.4423125928977, "min": 400, "max": 800, "type": "float"}
    safety_stock = 38.44231259290004  # OPT_PARAM: {"initial": 38.44231259290004, "min": 0, "max": 150, "type": "float"}
    demand_adjustment = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on recent pipeline arrivals
    recent_arrivals = pipeline_orders[:3] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent_demand = sum(recent_arrivals) / len(recent_arrivals) if recent_arrivals else 0

    # Adjust base stock based on demand pattern
    adjusted_base = base_stock + demand_adjustment * avg_recent_demand

    # Calculate target inventory position
    target_position = adjusted_base + safety_stock

    # Order amount to reach target
    order_amount = max(0, target_position - inventory_position)

    return order_amount
