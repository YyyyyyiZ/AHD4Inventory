# policy_hash: f35e6769d06a1a09fad93043b3135c3c4d67d2780b06ea83c126c5d69105e3db
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 74
# source_prompt_files: 1
# best_target_performance: 792.02
# best_prompt_performance: 792.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104146.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 290.99999999999005  # OPT_PARAM: {"initial": 290.99999999999005, "min": 250, "max": 320, "type": "float"}
    safety_stock = 25.0  # OPT_PARAM: {"initial": 25.0, "min": 15, "max": 40, "type": "float"}
    demand_sensitivity = 0.08  # OPT_PARAM: {"initial": 0.08, "min": 0.02, "max": 0.15, "type": "float"}
    pipeline_weight = 0.95  # OPT_PARAM: {"initial": 0.95, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    demand_window = 3  # OPT_PARAM: {"initial": 3, "min": 2, "max": 5, "type": "int"}

    # Calculate net inventory position with full pipeline weight
    weighted_pipeline = sum(p * (pipeline_weight ** i) for i, p in enumerate(reversed(pipeline_orders)))
    net_inventory = on_hand_inventory + weighted_pipeline

    # Estimate demand from recent pipeline arrivals using configurable window
    if len(pipeline_orders) >= demand_window:
        recent_arrivals = pipeline_orders[:demand_window]
        avg_demand = sum(recent_arrivals) / len(recent_arrivals)
    else:
        avg_demand = 100.0

    # Adjust base stock based on demand deviation
    demand_adjustment = demand_sensitivity * (avg_demand - 100)
    adjusted_base_stock = base_stock + demand_adjustment

    # Ensure minimum safety stock
    target_inventory = max(adjusted_base_stock, safety_stock)

    # Calculate raw order amount
    raw_order = max(0, target_inventory - net_inventory)

    # Apply smoothing with stronger emphasis on pipeline stability
    order_amount = int(round(raw_order * smoothing_factor + pipeline_orders[-1] * (1 - smoothing_factor)))

    return order_amount
