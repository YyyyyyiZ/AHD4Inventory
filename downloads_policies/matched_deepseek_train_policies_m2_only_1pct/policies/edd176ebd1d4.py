# policy_hash: edd176ebd1d47249b322786b43784f6666cc36f77bb499d8928ada21e381e2d4
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 1331.75
# best_prompt_performance: 1323.94
# best_rel_error_pct: 0.586446
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260128_144759.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 405.2756319915228  # OPT_PARAM: {"initial": 405.2756319915228, "min": 300, "max": 600, "type": "float"}
    safety_stock = 81.11078223995473  # OPT_PARAM: {"initial": 81.11078223995473, "min": 20, "max": 150, "type": "float"}
    smoothing_factor = 0.5329762325827683  # OPT_PARAM: {"initial": 0.5329762325827683, "min": 0.1, "max": 1.0, "type": "float"}
    demand_forecast_factor = 0.7331514094590182  # OPT_PARAM: {"initial": 0.7331514094590182, "min": 0.5, "max": 1.2, "type": "float"}
    pipeline_weight = 0.4667808847979793  # OPT_PARAM: {"initial": 0.4667808847979793, "min": 0.0, "max": 0.5, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders (as proxy for recent ordering patterns)
    # This helps anticipate future needs
    if len(pipeline_orders) > 0:
        avg_pipeline = sum(pipeline_orders) / len(pipeline_orders)
        demand_adjustment = demand_forecast_factor * avg_pipeline
    else:
        demand_adjustment = 0

    # Adjust target based on pipeline composition
    # If pipeline has high values, we might need less safety stock
    pipeline_variability = max(pipeline_orders) - min(pipeline_orders) if len(pipeline_orders) > 1 else 0
    pipeline_effect = pipeline_weight * pipeline_variability

    # Dynamic target inventory
    target_inventory = base_stock + safety_stock - pipeline_effect + demand_adjustment

    # Calculate order with smoothing
    raw_order = target_inventory - inventory_position
    order_amount = max(0, smoothing_factor * raw_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
