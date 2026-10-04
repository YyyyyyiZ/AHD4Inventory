# policy_hash: e8a24d25a57e9dbfadec31dc08fdcfb27c525840680ef7e6c23469ed71c45971
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_5
# matched_train_cells: 14
# source_prompt_files: 2
# best_target_performance: 11730.02
# best_prompt_performance: 11730.02
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_103211.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 418.2003424112832  # OPT_PARAM: {"initial": 418.2003424112832, "min": 350, "max": 500, "type": "float"}
    safety_stock = 53.20034241128281  # OPT_PARAM: {"initial": 53.20034241128281, "min": 40, "max": 80, "type": "float"}
    demand_estimate = 110.0  # OPT_PARAM: {"initial": 110.0, "min": 110, "max": 160, "type": "float"}
    pipeline_weight = 0.024523370547067713  # OPT_PARAM: {"initial": 0.024523370547067713, "min": 0.0, "max": 0.3, "type": "float"}
    recent_weight = 0.5568815112450802  # OPT_PARAM: {"initial": 0.5568815112450802, "min": 0.2, "max": 0.6, "type": "float"}
    min_order_factor = 0.4  # OPT_PARAM: {"initial": 0.4, "min": 0.4, "max": 0.8, "type": "float"}
    max_order_factor = 1.2  # OPT_PARAM: {"initial": 1.2, "min": 1.2, "max": 2.5, "type": "float"}
    holding_weight = 0.4660616900052937  # OPT_PARAM: {"initial": 0.4660616900052937, "min": 0.1, "max": 0.5, "type": "float"}
    lost_sales_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.5, "max": 0.9, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate pipeline components
    total_pipeline = sum(pipeline_orders)
    recent_pipeline = sum(pipeline_orders[:2])  # Next 2 periods' arrivals

    # Dynamic adjustments with cost-aware weighting
    pipeline_adjustment = pipeline_weight * total_pipeline
    recent_adjustment = recent_weight * recent_pipeline

    # Cost-aware target adjustment
    cost_adjustment = (holding_weight * on_hand_inventory -
                      lost_sales_weight * max(0, demand_estimate - on_hand_inventory))

    # Calculate target inventory position
    target_position = (base_stock + safety_stock - pipeline_adjustment +
                      recent_adjustment + cost_adjustment)

    # Calculate base order amount
    order_amount = max(0, target_position - inventory_position)

    # Apply demand-based minimum order
    min_order = max(0, min_order_factor * demand_estimate - pipeline_orders[-1] if pipeline_orders else min_order_factor * demand_estimate)
    order_amount = max(order_amount, min_order)

    # Apply maximum order limit based on demand estimate
    max_order = max_order_factor * demand_estimate
    order_amount = min(order_amount, max_order)

    # Round to nearest integer
    order_amount = int(round(order_amount))

    return order_amount
