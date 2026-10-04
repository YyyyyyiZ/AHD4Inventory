# policy_hash: 4b452c1545c2e6dc62c0d475cb47499542e6665bb1672a52106dccd465342579
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 5880.4
# best_prompt_performance: 5880.48
# best_rel_error_pct: 0.001360
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_030446.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 182.972361671152  # OPT_PARAM: {"initial": 182.972361671152, "min": 100, "max": 400, "type": "float"}
    safety_stock = 10.916848751197476  # OPT_PARAM: {"initial": 10.916848751197476, "min": 10, "max": 100, "type": "float"}
    demand_estimate = 52.140319591279656  # OPT_PARAM: {"initial": 52.140319591279656, "min": 50, "max": 300, "type": "float"}
    pipeline_coverage = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 2.0, "type": "float"}
    adjustment_smoothing = 0.1980269244494433  # OPT_PARAM: {"initial": 0.1980269244494433, "min": 0.1, "max": 0.8, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time plus review period
    lead_time_demand = demand_estimate * (len(pipeline_orders) + 1)

    # Calculate target inventory position considering pipeline coverage
    target_position = base_stock + safety_stock + pipeline_coverage * lead_time_demand

    # Smooth adjustment to avoid overreacting
    order_amount = max(0, target_position - inventory_position)
    order_amount = adjustment_smoothing * order_amount + (1 - adjustment_smoothing) * demand_estimate

    # Round to nearest integer
    return order_amount
