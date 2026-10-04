# policy_hash: dd0497be4630ac490542c5e1c424f036b2849c726990f74222ae2cdc08a43bf6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 29
# source_prompt_files: 1
# best_target_performance: 6082.8
# best_prompt_performance: 6082.8
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_095158.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 420.20000000004666  # OPT_PARAM: {"initial": 420.20000000004666, "min": 350, "max": 550, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.0, "type": "float"}
    smoothing_factor = 0.15000000000000002  # OPT_PARAM: {"initial": 0.15000000000000002, "min": 0.05, "max": 0.3, "type": "float"}
    safety_stock = 42.999999999578336  # OPT_PARAM: {"initial": 42.999999999578336, "min": 30, "max": 80, "type": "float"}
    demand_anticipation_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.0, "max": 1.2, "type": "float"}
    pipeline_lookback = 3  # OPT_PARAM: {"initial": 3, "min": 1, "max": 6, "type": "int"}

    # Calculate weighted pipeline sum (emphasize near-term arrivals)
    total_pipeline = 0.0
    for i, qty in enumerate(pipeline_orders[:pipeline_lookback]):
        weight = 1.0 - (i * 0.15)  # Higher weight for imminent arrivals
        total_pipeline += qty * weight

    # Effective pipeline
    effective_pipeline = total_pipeline * pipeline_weight

    # Inventory position
    inventory_position = on_hand_inventory + effective_pipeline

    # Adjusted base stock with safety buffer
    adjusted_base_stock = base_stock * demand_anticipation_factor + safety_stock

    # Order quantity
    raw_order = max(0, adjusted_base_stock - inventory_position)

    # Apply stronger smoothing for stability
    if raw_order > 0:
        order_amount = int(raw_order * smoothing_factor + 0.5)
    else:
        order_amount = 0

    return order_amount
