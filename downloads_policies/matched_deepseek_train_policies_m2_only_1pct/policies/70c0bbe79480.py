# policy_hash: 70c0bbe79480c4f60e96ca5227464b3d70844b83e16a05076d0ed78e72e84132
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 1
# source_prompt_files: 1
# best_target_performance: 7205.89
# best_prompt_performance: 7205.24
# best_rel_error_pct: 0.009020
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251222_034421.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 356.962137444324  # OPT_PARAM: {"initial": 356.962137444324, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 50.00198000169216  # OPT_PARAM: {"initial": 50.00198000169216, "min": 0, "max": 200, "type": "float"}
    pipeline_factor = 1.1653664436492337  # OPT_PARAM: {"initial": 1.1653664436492337, "min": 0.1, "max": 1.5, "type": "float"}

    # Calculate effective inventory position
    effective_inventory = on_hand_inventory + pipeline_factor * sum(pipeline_orders)

    # Calculate target inventory position
    target = base_stock + safety_stock

    # Place order to reach target
    order_amount = max(0, target - effective_inventory)

    # Round to nearest integer since demand is integer
    order_amount = int(round(order_amount))

    return order_amount
