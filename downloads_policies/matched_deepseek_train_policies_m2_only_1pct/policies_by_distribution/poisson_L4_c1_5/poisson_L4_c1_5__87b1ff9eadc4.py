# policy_hash: 87b1ff9eadc465d4ec988582c355923ebf36c2d755942f23ee242448c08a89ed
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 24800.6
# best_prompt_performance: 24800.6
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_081137.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 550.0  # OPT_PARAM: {"initial": 550.0, "min": 400, "max": 700, "type": "float"}
    safety_stock = 100.0  # OPT_PARAM: {"initial": 100.0, "min": 50, "max": 200, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time (L=4)
    # Using average of recent demands from pipeline as proxy
    if len(pipeline_orders) >= 2:
        recent_orders = pipeline_orders[-2:]  # Last two orders placed
        avg_recent_demand = sum(recent_orders) / len(recent_orders)
    else:
        avg_recent_demand = 100.0  # Default average demand

    # Adjust base stock based on recent demand pattern
    dynamic_base = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 1.0, "max": 4.0, "type": "float"}

    # Calculate order-up-to level with safety stock
    order_up_to = 4.0  # OPT_PARAM: {"initial": 4.0, "min": 3.0, "max": 5.0, "type": "float"}

    # Calculate order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Round to nearest integer (since demand is integer)
    order_amount = int(round(order_amount))

    return order_amount
