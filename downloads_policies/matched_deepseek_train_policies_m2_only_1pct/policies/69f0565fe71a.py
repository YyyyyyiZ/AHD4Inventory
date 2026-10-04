# policy_hash: 69f0565fe71aaca8b18f4601cd876c01e3b3a846ebd7ce017311abb3f21cc4d6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 8
# source_prompt_files: 1
# best_target_performance: 1335.66
# best_prompt_performance: 1335.66
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_070607.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 311.0787205781342  # OPT_PARAM: {"initial": 311.0787205781342, "min": 280, "max": 380, "type": "float"}
    safety_stock = 30.642300664802562  # OPT_PARAM: {"initial": 30.642300664802562, "min": 15, "max": 60, "type": "float"}
    adjustment_factor = 0.738362366695467  # OPT_PARAM: {"initial": 0.738362366695467, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 20.0  # OPT_PARAM: {"initial": 20.0, "min": 5, "max": 40, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Use average of next two arrivals as demand indicator
    if len(pipeline_orders) >= 2:
        upcoming_demand_indicator = (pipeline_orders[0] + pipeline_orders[1]) / 2
    else:
        upcoming_demand_indicator = base_stock / 3

    # Dynamic target adjustment based on upcoming demand
    dynamic_adjustment = max(0, upcoming_demand_indicator - base_stock/3)
    target_inventory = base_stock + safety_stock + min(demand_buffer, dynamic_adjustment)

    # Calculate order amount with smoother adjustment
    raw_order = max(0, target_inventory - inventory_position)

    # Apply non-linear adjustment for better responsiveness
    if raw_order > base_stock * 0.3:
        adjusted_order = raw_order * adjustment_factor
    else:
        # Order smaller amounts more conservatively
        adjusted_order = raw_order * (adjustment_factor * 0.8)

    # Round to nearest integer
    order_amount = int(round(adjusted_order))

    return order_amount
