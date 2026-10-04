# policy_hash: 6adaf5e871eba6a75708406717eb2bf8e1ef979e5097f0569c96f7b1a82be38e
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 3099.58
# best_prompt_performance: 3094.04
# best_rel_error_pct: 0.178734
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_050436.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 683.6234136212577  # OPT_PARAM: {"initial": 683.6234136212577, "min": 400, "max": 700, "type": "float"}
    safety_stock = 98.89452324498906  # OPT_PARAM: {"initial": 98.89452324498906, "min": 30, "max": 100, "type": "float"}
    adjustment_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_estimate_window = 4  # OPT_PARAM: {"initial": 4, "min": 2, "max": 6, "type": "int"}
    demand_buffer_factor = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 1.0, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate recent demand from pipeline orders (arriving orders reflect past demand)
    if len(pipeline_orders) >= demand_estimate_window:
        recent_demand = sum(pipeline_orders[-demand_estimate_window:]) / demand_estimate_window
    else:
        recent_demand = 100.0  # default estimate

    # Dynamic target adjusts to recent demand
    dynamic_target = base_stock + safety_stock * demand_buffer_factor

    # Order-up-to policy with partial adjustment
    order_amount = max(0, (dynamic_target - net_inventory) * adjustment_factor)

    # Add small buffer based on recent demand variability
    if order_amount > 0:
        order_amount += recent_demand * 0.05

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
