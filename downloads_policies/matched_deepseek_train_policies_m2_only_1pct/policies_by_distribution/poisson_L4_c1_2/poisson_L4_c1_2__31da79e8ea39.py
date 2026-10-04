# policy_hash: 31da79e8ea39f7528009f81c009a05471788cbc92d078259c657d740738d5e6d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 13
# source_prompt_files: 1
# best_target_performance: 1727.95
# best_prompt_performance: 1727.95
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_235041.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 450.1  # OPT_PARAM: {"initial": 450.1, "min": 300, "max": 600, "type": "float"}
    demand_estimate = 94.30422935331461  # OPT_PARAM: {"initial": 94.30422935331461, "min": 80, "max": 120, "type": "float"}
    safety_factor = 1.1105447674962068  # OPT_PARAM: {"initial": 1.1105447674962068, "min": 0.5, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = 4 * demand_estimate

    # Calculate safety stock based on demand variability
    safety_stock = safety_factor * demand_estimate

    # Calculate target inventory position
    target_position = lead_time_demand + safety_stock

    # Calculate order amount using base-stock policy
    order_amount = max(0, target_position - inventory_position)

    # Round to nearest integer
    return order_amount
