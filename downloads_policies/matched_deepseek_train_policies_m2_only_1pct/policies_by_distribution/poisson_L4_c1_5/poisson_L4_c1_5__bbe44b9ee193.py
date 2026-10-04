# policy_hash: bbe44b9ee193e3b88710ddbc6ce926d303d77d73de0aa81c375aaa4361e3a29d
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 2060.12
# best_prompt_performance: 2060.12
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_082057.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 516.6133278602058  # OPT_PARAM: {"initial": 516.6133278602058, "min": 400, "max": 600, "type": "float"}
    safety_stock = 37.563589751549515  # OPT_PARAM: {"initial": 37.563589751549515, "min": 20, "max": 100, "type": "float"}
    pipeline_factor = 0.9655734719003762  # OPT_PARAM: {"initial": 0.9655734719003762, "min": 0.5, "max": 1.0, "type": "float"}
    demand_buffer = 13.172776165152612  # OPT_PARAM: {"initial": 13.172776165152612, "min": 0, "max": 50, "type": "float"}
    smoothing_factor = 0.6033166428560688  # OPT_PARAM: {"initial": 0.6033166428560688, "min": 0.1, "max": 1.0, "type": "float"}

    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Adjust target based on pipeline coverage
    pipeline_coverage = sum(pipeline_orders) / len(pipeline_orders) if pipeline_orders else 0
    adjusted_safety = safety_stock * (1.0 - pipeline_factor * pipeline_coverage / base_stock)

    target = base_stock + adjusted_safety + demand_buffer

    # Calculate order with smoothing
    raw_order = max(0, target - inventory_position)
    order_amount = int(round(raw_order * smoothing_factor))

    # Ensure minimum order if we're significantly below target
    if inventory_position < target * 0.8:
        order_amount = max(order_amount, int(round(target * 0.1)))

    return order_amount
