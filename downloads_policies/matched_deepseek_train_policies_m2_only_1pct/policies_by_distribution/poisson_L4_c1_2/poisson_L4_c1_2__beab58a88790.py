# policy_hash: beab58a88790a696303261fbb70b7ff71c0b3975b2a36856e36e1e58c1fb8e34
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 735.0
# best_prompt_performance: 735.0
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260130_031145.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 529.2668516280546  # OPT_PARAM: {"initial": 529.2668516280546, "min": 450, "max": 650, "type": "float"}
    lead_time = 4

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Calculate base order amount
    order_amount = max(0, base_stock - net_inventory)

    # Apply proportional adjustment based on pipeline status
    pipeline_factor = 0.7091421867902422  # OPT_PARAM: {"initial": 0.7091421867902422, "min": 0.5, "max": 1.2, "type": "float"}
    order_amount = order_amount * pipeline_factor

    # Add safety stock adjustment based on recent pipeline arrivals
    safety_adjustment = 10.534418947980436  # OPT_PARAM: {"initial": 10.534418947980436, "min": 5, "max": 40, "type": "float"}
    if pipeline_orders[0] < 80:  # If recent arrival was low
        order_amount = order_amount + safety_adjustment

    # Apply reasonable bounds
    max_order = 96.67590892330287  # OPT_PARAM: {"initial": 96.67590892330287, "min": 90, "max": 180, "type": "float"}
    min_order = 10.0  # OPT_PARAM: {"initial": 10.0, "min": 0, "max": 20, "type": "float"}

    if order_amount > max_order:
        order_amount = max_order
    elif order_amount < min_order:
        order_amount = min_order

    # Round to nearest integer
    return order_amount
