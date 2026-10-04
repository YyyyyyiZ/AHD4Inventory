# policy_hash: 82fcd2bcd5ffa32d6991c9ab9dc61ae29b331a2b0e4d8f36f42f26be646f5ac3
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L2_c1_5
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 10794.88
# best_prompt_performance: 10794.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_031910.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.38267231877666  # OPT_PARAM: {"initial": 308.38267231877666, "min": 200, "max": 600, "type": "float"}
    safety_stock = 28.382672318774336  # OPT_PARAM: {"initial": 28.382672318774336, "min": 10, "max": 100, "type": "float"}
    pipeline_weight = 0.2603950963660945  # OPT_PARAM: {"initial": 0.2603950963660945, "min": 0.0, "max": 0.5, "type": "float"}
    demand_estimate_factor = 0.3101617152829502  # OPT_PARAM: {"initial": 0.3101617152829502, "min": 0.3, "max": 1.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate future demand using pipeline orders as indicator
    if pipeline_orders:
        # Use weighted average of recent pipeline orders as demand estimate
        weights = [0.5, 0.3, 0.2]  # More weight to recent orders
        weighted_sum = 0
        for i, qty in enumerate(pipeline_orders[-3:]):  # Last 3 orders
            if i < len(weights):
                weighted_sum += qty * weights[i]
        estimated_demand = weighted_sum * demand_estimate_factor
    else:
        estimated_demand = 0

    # Adjust base stock based on estimated demand
    adjusted_base_stock = base_stock + estimated_demand

    # Simple pipeline adjustment (reduce order when pipeline is large)
    pipeline_total = sum(pipeline_orders)
    pipeline_adjustment = max(0, 1.0 - pipeline_weight * pipeline_total / adjusted_base_stock)

    # Final target inventory level
    target_inventory = adjusted_base_stock * pipeline_adjustment + safety_stock

    # Order amount to reach target
    order_amount = max(0, target_inventory - inventory_position)

    # Round to integer
    return order_amount
