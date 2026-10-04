# policy_hash: 7914cc6c0da3ff463f1d176e06315840a638d4cb87a4f825a60e571747cd9615
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L6_c1_2
# matched_train_cells: 16
# source_prompt_files: 1
# best_target_performance: 2258.06
# best_prompt_performance: 2257.91
# best_rel_error_pct: 0.006643
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_074143.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 582.8332936990706  # OPT_PARAM: {"initial": 582.8332936990706, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 37.91434189230215  # OPT_PARAM: {"initial": 37.91434189230215, "min": 0, "max": 200, "type": "float"}
    demand_buffer = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 0, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand from pipeline arrivals
    upcoming_arrivals = sum(pipeline_orders[:3])  # Next 3 periods of arrivals

    # Adjust base stock based on upcoming arrivals and safety stock
    adjusted_base = base_stock + safety_stock
    if upcoming_arrivals < demand_buffer:
        adjusted_base += (demand_buffer - upcoming_arrivals) * 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 1.0, "type": "float"}

    # Calculate order amount with smoothing
    raw_order = adjusted_base - inventory_position
    if raw_order > 0:
        # Smooth large orders to avoid over-ordering
        order_amount = 87.35923793788778  # OPT_PARAM: {"initial": 87.35923793788778, "min": 50, "max": 300, "type": "float"}
    else:
        order_amount = 0

    return order_amount
