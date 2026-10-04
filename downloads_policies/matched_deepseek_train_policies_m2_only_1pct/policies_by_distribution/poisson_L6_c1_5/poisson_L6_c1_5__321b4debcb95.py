# policy_hash: 321b4debcb95b4527e2ab387ea07dd371589e54709ff5f00f00f12d700acffac
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_5
# matched_train_cells: 2
# source_prompt_files: 1
# best_target_performance: 3138.77
# best_prompt_performance: 3139.34
# best_rel_error_pct: 0.018160
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_054402.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 500.0  # OPT_PARAM: {"initial": 500.0, "min": 300, "max": 700, "type": "float"}
    safety_factor = 1.923854339972519  # OPT_PARAM: {"initial": 1.923854339972519, "min": 0.5, "max": 3.0, "type": "float"}
    avg_demand = 104.78155616290964  # OPT_PARAM: {"initial": 104.78155616290964, "min": 80, "max": 120, "type": "float"}
    lead_time = 6  # Fixed lead time

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate target inventory level
    # Base stock covers average lead time demand
    # Safety stock covers demand variability during lead time
    demand_std = 15.18549826001346  # OPT_PARAM: {"initial": 15.18549826001346, "min": 5, "max": 30, "type": "float"}
    safety_stock = safety_factor * demand_std * (lead_time ** 0.5)
    target_inventory = avg_demand * lead_time + safety_stock

    # Calculate order-up-to level
    order_up_to = max(0, target_inventory - inventory_position)

    # Apply base stock as upper bound to prevent excessive ordering
    if order_up_to > base_stock:
        order_up_to = base_stock

    # Round to nearest integer
    order_amount = int(round(order_up_to))

    return order_amount
