# policy_hash: 572d0f7791ea634617e0dbc93f79958641ac79dcf58fe8d289bf287dc8aa518f
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: poisson_L2_c1_2
# matched_train_cells: 4
# source_prompt_files: 1
# best_target_performance: 912.86
# best_prompt_performance: 912.86
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_poisson_L2_c1_2_50_plain_processed_scipy_15_default_m2_4_r1/prompt_for_code/m2_20251217_223619.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 321.65707155245315  # OPT_PARAM: {"initial": 321.65707155245315, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 46.457683608245226  # OPT_PARAM: {"initial": 46.457683608245226, "min": 0, "max": 150, "type": "float"}
    demand_buffer = 0.5573825690944969  # OPT_PARAM: {"initial": 0.5573825690944969, "min": 0.5, "max": 2.0, "type": "float"}

    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)

    # Estimate upcoming demand based on pipeline arrivals
    # Weight recent pipeline orders more heavily
    if len(pipeline_orders) >= 2:
        recent_demand_estimate = (pipeline_orders[-1] + pipeline_orders[-2]) / 2 if len(pipeline_orders) >= 2 else pipeline_orders[-1]
    else:
        recent_demand_estimate = base_stock / 3

    # Adjust base stock based on recent demand pattern
    adjusted_base = base_stock * (1 + (recent_demand_estimate - base_stock/3) / (base_stock/3) * 0.1)

    # Calculate target inventory position
    target = max(base_stock, adjusted_base) + safety_stock

    # Calculate order amount with demand buffer
    order_needed = max(0, target - net_inventory)

    # Add buffer for expected demand
    order_amount = max(0, order_needed * demand_buffer)

    # Round to nearest integer (since order amounts should be integers)
    return order_amount
