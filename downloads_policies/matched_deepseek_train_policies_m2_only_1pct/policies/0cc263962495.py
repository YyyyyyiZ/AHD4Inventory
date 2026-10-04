# policy_hash: 0cc263962495be80103de4c4a055d5d281843c61b40380b19c047c5ec997ddbb
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L4_c1_5
# matched_train_cells: 15
# source_prompt_files: 2
# best_target_performance: 1327.1
# best_prompt_performance: 1327.1
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L4_c1_5_50_plain_processed_scipy_15_default_m2_4_r3/prompt_for_code/m2_20251218_082959.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 496.61888790270916  # OPT_PARAM: {"initial": 496.61888790270916, "min": 450, "max": 600, "type": "float"}
    demand_forecast = 96.29433202292677  # OPT_PARAM: {"initial": 96.29433202292677, "min": 95, "max": 105, "type": "float"}
    smoothing_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 0.5, "type": "float"}
    safety_stock = 60.0  # OPT_PARAM: {"initial": 60.0, "min": 40, "max": 100, "type": "float"}
    lead_time_factor = 1.1  # OPT_PARAM: {"initial": 1.1, "min": 1.0, "max": 1.3, "type": "float"}
    lost_sales_weight = 1.8  # OPT_PARAM: {"initial": 1.8, "min": 1.0, "max": 3.0, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Calculate expected demand during lead time
    lead_time_demand = lead_time_factor * demand_forecast * len(pipeline_orders)

    # Adjust safety stock based on cost ratio
    adjusted_safety_stock = safety_stock * lost_sales_weight

    # Calculate target inventory level
    target_inventory = lead_time_demand + adjusted_safety_stock

    # Use the maximum of base_stock and target_inventory
    order_up_to = max(base_stock, target_inventory)

    # Calculate required order
    required_order = max(0, order_up_to - inventory_position)

    # Smooth adjustment with demand forecast
    smoothed_order = smoothing_factor * required_order + (1 - smoothing_factor) * demand_forecast

    # Ensure non-negative integer order
    order_amount = max(0, round(smoothed_order))

    return order_amount
