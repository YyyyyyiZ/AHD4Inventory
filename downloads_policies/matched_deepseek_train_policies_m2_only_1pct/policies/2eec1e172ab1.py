# policy_hash: 2eec1e172ab1c9aca52b422f717d7b42eb12cfec8860de98350d4c89f3a87225
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: exponential_L6_c1_2
# matched_train_cells: 7
# source_prompt_files: 1
# best_target_performance: 6586.72
# best_prompt_performance: 6584.8
# best_rel_error_pct: 0.029150
# example_source_txt: examples/inventory/deepseek-chat_exponential_L6_c1_2_50_plain_processed_scipy_15_default_m2_4_r2/prompt_for_code/m2_20251218_052815.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 358.77672578617916  # OPT_PARAM: {"initial": 358.77672578617916, "min": 100, "max": 800, "type": "float"}
    safety_stock = 21.425502124026327  # OPT_PARAM: {"initial": 21.425502124026327, "min": 20, "max": 200, "type": "float"}
    smoothing_factor = 0.5674178685423422  # OPT_PARAM: {"initial": 0.5674178685423422, "min": 0.5, "max": 1.0, "type": "float"}
    demand_forecast = 116.53717302891442  # OPT_PARAM: {"initial": 116.53717302891442, "min": 50, "max": 300, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Simple base-stock policy with smoothing
    target_inventory = base_stock + safety_stock
    raw_order = max(0, target_inventory - inventory_position)

    # Apply smoothing to avoid extreme order fluctuations
    smoothed_order = smoothing_factor * raw_order + (1 - smoothing_factor) * demand_forecast

    # Ensure integer order amount
    order_amount = int(round(smoothed_order))

    return order_amount
