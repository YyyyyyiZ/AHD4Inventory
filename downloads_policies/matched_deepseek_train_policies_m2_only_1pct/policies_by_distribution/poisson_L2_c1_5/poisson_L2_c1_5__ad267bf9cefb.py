# policy_hash: ad267bf9cefb9f1bdeb3c259381d5f7e83f32701a559104070720d1cf16fa5a2
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 1373.18
# best_prompt_performance: 1373.18
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_231135.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 300.4052131005404  # OPT_PARAM: {"initial": 300.4052131005404, "min": 200, "max": 400, "type": "float"}
    safety_stock = 45.4052131005425  # OPT_PARAM: {"initial": 45.4052131005425, "min": 0, "max": 100, "type": "float"}
    adjustment_factor = 0.6  # OPT_PARAM: {"initial": 0.6, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 21.967184590169943  # OPT_PARAM: {"initial": 21.967184590169943, "min": 0, "max": 50, "type": "float"}

    # Calculate current inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand from pipeline orders (as proxy for recent demand)
    recent_demand_estimate = max(pipeline_orders) if pipeline_orders else 0

    # Dynamic target that adjusts to recent demand patterns
    dynamic_target = base_stock + safety_stock + demand_buffer * (recent_demand_estimate / 100)

    # Calculate order amount with adjustment factor
    raw_order = max(0, dynamic_target - inventory_position)
    order_amount = int(round(adjustment_factor * raw_order))

    return order_amount
