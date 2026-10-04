# policy_hash: 3d0238aa01b73b452845876a4c04b08c8616c4805755d65b481b7d43669b2845
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_2
# matched_train_cells: 9
# source_prompt_files: 1
# best_target_performance: 802.5
# best_prompt_performance: 802.5
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_035455.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 400.19890791142825  # OPT_PARAM: {"initial": 400.19890791142825, "min": 380, "max": 480, "type": "float"}
    safety_stock = 63.38434283402528  # OPT_PARAM: {"initial": 63.38434283402528, "min": 60, "max": 120, "type": "float"}
    demand_estimate = 92.35685043870998  # OPT_PARAM: {"initial": 92.35685043870998, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.8  # OPT_PARAM: {"initial": 0.8, "min": 0.8, "max": 1.2, "type": "float"}
    lead_time = 4  # Fixed lead time

    # Calculate inventory position with full pipeline weight
    inventory_position = on_hand_inventory + sum(pipeline_orders) * pipeline_weight

    # Calculate expected demand during lead time plus one period (for coverage)
    expected_lead_time_demand = demand_estimate * (lead_time + 1)

    # Calculate target inventory position
    target_inventory = base_stock + safety_stock

    # Calculate order amount
    order_amount = max(0, target_inventory - inventory_position)

    # Apply smoothing to reduce order volatility
    smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * demand_estimate

    # Round to nearest integer
    order_amount = int(round(smoothed_order))

    return order_amount
