# policy_hash: 25b38d3aa7c7d8bce277ccefaff1f5793305d9bb81a6fa6a419d5c2e25c207db
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L6_c1_5
# matched_train_cells: 6
# source_prompt_files: 1
# best_target_performance: 3098.92
# best_prompt_performance: 3104.35
# best_rel_error_pct: 0.175222
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L6_c1_5_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260128_031933.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 649.9524069639835  # OPT_PARAM: {"initial": 649.9524069639835, "min": 300, "max": 800, "type": "float"}
    safety_stock = 149.79059902475223  # OPT_PARAM: {"initial": 149.79059902475223, "min": 0, "max": 150, "type": "float"}
    smoothing_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 0.9475295954363083  # OPT_PARAM: {"initial": 0.9475295954363083, "min": 0.8, "max": 1.5, "type": "float"}
    min_order = 0  # OPT_PARAM: {"initial": 0, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    upcoming_arrivals = pipeline_orders[0] if pipeline_orders else 0

    # Adjust base stock based on upcoming arrivals
    adjusted_base = base_stock * (1.0 - 0.1 * min(upcoming_arrivals / (base_stock + 1), 1.0))

    # Calculate target inventory position with safety stock
    target_position = adjusted_base + safety_stock

    # Calculate order amount with smoothing
    raw_order = smoothing_factor * (target_position - inventory_position)

    # Apply demand buffer to prevent stockouts
    buffered_order = raw_order * demand_buffer

    # Ensure minimum order quantity
    order_amount = max(min_order, buffered_order)

    # Round to nearest integer
    return order_amount
