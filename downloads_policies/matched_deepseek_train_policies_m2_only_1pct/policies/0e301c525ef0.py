# policy_hash: 0e301c525ef016def5ad3a708bf4a95427cd3d5a1d34ccd54fa69d7f8ed563df
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 20
# source_prompt_files: 1
# best_target_performance: 1025.54
# best_prompt_performance: 1024.1
# best_rel_error_pct: 0.140414
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_075449.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 419.9772192921864  # OPT_PARAM: {"initial": 419.9772192921864, "min": 350, "max": 500, "type": "float"}
    safety_stock = 34.977219292186376  # OPT_PARAM: {"initial": 34.977219292186376, "min": 20, "max": 50, "type": "float"}
    demand_forecast = 98.70037006374554  # OPT_PARAM: {"initial": 98.70037006374554, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.25, "type": "float"}
    pipeline_weight = 0.9  # OPT_PARAM: {"initial": 0.9, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected incoming inventory from pipeline
    expected_pipeline = pipeline_weight * sum(pipeline_orders)

    # Modified base-stock target that accounts for pipeline reliability
    effective_base_stock = base_stock + safety_stock - (1 - pipeline_weight) * sum(pipeline_orders)

    # Calculate raw order quantity
    raw_order = max(0, effective_base_stock - inventory_position)

    # Apply smoothing with demand forecast adjustment
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure order doesn't drop below forecast when inventory is low
    if inventory_position < base_stock:
        smoothed_order = max(smoothed_order, demand_forecast * 0.8)

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
