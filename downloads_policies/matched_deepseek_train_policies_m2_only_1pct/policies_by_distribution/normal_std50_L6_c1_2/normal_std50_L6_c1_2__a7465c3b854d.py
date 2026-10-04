# policy_hash: a7465c3b854d6d82aadbb579ecd22176c519b6dc9c15f865076c4aa3e63c3702
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std50_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 3977.72
# best_prompt_performance: 3976.54
# best_rel_error_pct: 0.029665
# example_source_txt: examples/inventory/deepseek-chat_normal_std50_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251216_231704.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 585.0017042198575  # OPT_PARAM: {"initial": 585.0017042198575, "min": 400, "max": 800, "type": "float"}
    safety_stock = 111.54610198764641  # OPT_PARAM: {"initial": 111.54610198764641, "min": 50, "max": 200, "type": "float"}
    smoothing_factor = 0.2  # OPT_PARAM: {"initial": 0.2, "min": 0.2, "max": 0.5, "type": "float"}
    demand_multiplier = 2.0  # OPT_PARAM: {"initial": 2.0, "min": 1.0, "max": 2.0, "type": "float"}
    pipeline_weight = 1.0  # OPT_PARAM: {"initial": 1.0, "min": 0.1, "max": 1.0, "type": "float"}
    min_order = 20  # OPT_PARAM: {"initial": 20, "min": 0, "max": 50, "type": "int"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand using weighted pipeline orders
    if len(pipeline_orders) > 0:
        # Weight recent orders more heavily
        weights = []
        total_weight = 0
        weighted_sum = 0

        for i, order in enumerate(reversed(pipeline_orders)):
            weight = pipeline_weight ** i
            weights.append(weight)
            total_weight += weight
            weighted_sum += order * weight

        if total_weight > 0:
            estimated_demand = (weighted_sum / total_weight) * demand_multiplier
        else:
            estimated_demand = 0
    else:
        estimated_demand = 0

    # Calculate target inventory level
    target_inventory = base_stock + safety_stock + estimated_demand

    # Calculate order needed to reach target
    order_needed = max(0, target_inventory - inventory_position)

    # Apply smoothing to prevent large order swings
    order_amount = smoothing_factor * order_needed

    # Add minimum order to maintain pipeline flow
    order_amount = max(order_amount, min_order)

    # Ensure order is integer and non-negative
    order_amount = int(round(order_amount))

    return order_amount
