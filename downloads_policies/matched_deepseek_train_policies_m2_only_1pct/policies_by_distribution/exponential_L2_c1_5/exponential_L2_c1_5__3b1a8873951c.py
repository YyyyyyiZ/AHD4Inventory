# policy_hash: 3b1a8873951c60449bab4d13e7cb8a2dd3b2981aa59060a16f3410fd56791010
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 26
# source_prompt_files: 2
# best_target_performance: 10168.64
# best_prompt_performance: 10168.64
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_233223.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 320.39106191853557  # OPT_PARAM: {"initial": 320.39106191853557, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 46.12586581393564  # OPT_PARAM: {"initial": 46.12586581393564, "min": 0, "max": 200, "type": "float"}
    demand_forecast_factor = 0.2685789884000892  # OPT_PARAM: {"initial": 0.2685789884000892, "min": 0.1, "max": 2.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on pipeline composition
    # Give more weight to near-term arrivals
    weighted_pipeline = 0
    for i, q in enumerate(pipeline_orders):
        weight = 1.0 / (i + 1)  # Higher weight for earlier arrivals
        weighted_pipeline += q * weight

    # Adjust target based on pipeline distribution
    pipeline_factor = 1.0 + (weighted_pipeline / (sum(pipeline_orders) + 1e-6) - 1.0) * 0.2

    # Calculate target inventory position
    target = base_stock * pipeline_factor + safety_stock

    # Calculate order amount
    order_amount = max(0, target - inventory_position)

    # Apply smoothing to avoid extreme orders
    smoothing_factor = 0.38188091053537004  # OPT_PARAM: {"initial": 0.38188091053537004, "min": 0.1, "max": 1.0, "type": "float"}
    if order_amount > 0:
        # Smooth large orders
        order_amount = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_forecast_factor * base_stock / (len(pipeline_orders) + 1)

    # Round to integer (as required by problem statement)
    return order_amount
