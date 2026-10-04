# policy_hash: 46f2a17268e0d3a2fb42c176b133e01b60e17c87b540cffa538c42391f178be5
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std30_L4_c1_2
# matched_train_cells: 131
# source_prompt_files: 1
# best_target_performance: 2210.76
# best_prompt_performance: 2210.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std30_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r6/prompt_for_code/m2_20260129_014000.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 466.7086424235026  # OPT_PARAM: {"initial": 466.7086424235026, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.012807162335925  # OPT_PARAM: {"initial": 50.012807162335925, "min": 0, "max": 200, "type": "float"}
    demand_alpha = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.01, "max": 0.5, "type": "float"}

    # Estimate recent demand from pipeline arrivals
    recent_arrivals = pipeline_orders[0] if pipeline_orders else 0
    estimated_demand = recent_arrivals * (1 + demand_alpha)

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust base stock based on demand estimate
    adjusted_base = base_stock * (estimated_demand / 100) if recent_arrivals > 0 else base_stock

    # Calculate order-up-to level with safety stock
    order_up_to = max(adjusted_base, safety_stock + estimated_demand * len(pipeline_orders))

    # Order amount
    order_amount = max(0, order_up_to - inventory_position)

    # Smooth ordering with maximum order limit
    max_order = 85.62288973489002  # OPT_PARAM: {"initial": 85.62288973489002, "min": 50, "max": 500, "type": "float"}
    order_amount = min(order_amount, max_order)

    return order_amount
