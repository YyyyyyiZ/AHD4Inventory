# policy_hash: 1e2a9394d562a2f86ae0313a8d141a7824afd4d4b55d778d3863b48b61c0e43d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 3
# source_prompt_files: 1
# best_target_performance: 1609.88
# best_prompt_performance: 1609.88
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_061306.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 234.38017897419155  # OPT_PARAM: {"initial": 234.38017897419155, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 6.326183308697059  # OPT_PARAM: {"initial": 6.326183308697059, "min": 0, "max": 100, "type": "float"}
    demand_adj_factor = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 1.5, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline orders (as proxy for recent demand)
    # Use average of recent orders as demand estimate
    if len(pipeline_orders) > 0:
        recent_orders_avg = sum(pipeline_orders) / len(pipeline_orders)
        estimated_demand = recent_orders_avg * demand_adj_factor
    else:
        estimated_demand = 0

    # Adjust base stock based on estimated demand and safety stock
    adjusted_base_stock = base_stock + safety_stock + estimated_demand

    # Calculate order amount
    order_amount = max(0, adjusted_base_stock - net_inventory)

    # Round to nearest integer (since order amounts should be integers)
    order_amount = int(round(order_amount))

    return order_amount
