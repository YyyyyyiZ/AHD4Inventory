# policy_hash: c00d6be3fd23badafd64b952d4bd937c81d89d4dd0d8a0995a18ff5c440e45e6
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_5
# matched_train_cells: 14
# source_prompt_files: 1
# best_target_performance: 1427.25
# best_prompt_performance: 1427.25
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_5_50_plain_processed_scipy_15_default_m2_4_r4/prompt_for_code/m2_20251218_104716.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 308.9814814814807  # OPT_PARAM: {"initial": 308.9814814814807, "min": 10, "max": 1000, "type": "float"}
    order_amount = max(0, base_stock - on_hand_inventory - sum(pipeline_orders))
    return order_amount
