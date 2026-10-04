# policy_hash: b36f54192f40007901e4a218093aa76b0179638ec4819a15f014d84db5b32505
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L6_c1_2
# matched_train_cells: 5
# source_prompt_files: 1
# best_target_performance: 761.03
# best_prompt_performance: 761.02
# best_rel_error_pct: 0.001314
# example_source_txt: examples/inventory/deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_023312.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 520.0  # OPT_PARAM: {"initial": 520.0, "min": 300, "max": 700, "type": "float"}
    safety_stock = 97.41650816235327  # OPT_PARAM: {"initial": 97.41650816235327, "min": 0, "max": 100, "type": "float"}
    demand_forecast = 118.18405913402773  # OPT_PARAM: {"initial": 118.18405913402773, "min": 80, "max": 120, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    expected_demand_during_leadtime = demand_forecast * len(pipeline_orders)

    # Calculate target inventory position
    target_position = expected_demand_during_leadtime + safety_stock

    # Order up to target, but ensure non-negative
    order_amount = max(0, target_position - inventory_position)

    # Cap order amount to avoid excessive ordering
    max_order = 95.96780670354589  # OPT_PARAM: {"initial": 95.96780670354589, "min": 80, "max": 200, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
