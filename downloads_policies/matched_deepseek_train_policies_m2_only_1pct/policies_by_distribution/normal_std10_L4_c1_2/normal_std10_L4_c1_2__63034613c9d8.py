# policy_hash: 63034613c9d85cf61ebaccf52255fba0aa079849a97d4439f001d88c169d30af
# source_scope: deepseek-chat exact m2 folders only; prompt_for_code/m2_*.txt only
# distributions: normal_std10_L4_c1_2
# matched_train_cells: 15
# source_prompt_files: 1
# best_target_performance: 1035.76
# best_prompt_performance: 1035.76
# best_rel_error_pct: 0.000000
# example_source_txt: examples/inventory/deepseek-chat_normal_std10_L4_c1_2_50_plain_processed_scipy_15_default_m2_2_r7/prompt_for_code/m2_20260130_044742.txt

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 451.01766001747495  # OPT_PARAM: {"initial": 451.01766001747495, "min": 300, "max": 700, "type": "float"}
    safety_stock = 26.117660017475128  # OPT_PARAM: {"initial": 26.117660017475128, "min": 0, "max": 100, "type": "float"}
    smoothing_factor = 0.06271063794493814  # OPT_PARAM: {"initial": 0.06271063794493814, "min": 0.0, "max": 0.5, "type": "float"}
    demand_forecast_factor = 0.020903545981646038  # OPT_PARAM: {"initial": 0.020903545981646038, "min": 0.0, "max": 0.3, "type": "float"}
    pipeline_weight = 0.010451772990823019  # OPT_PARAM: {"initial": 0.010451772990823019, "min": 0.0, "max": 0.2, "type": "float"}

    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)

    # Estimate future demand based on recent pipeline arrivals
    if len(pipeline_orders) >= 2:
        recent_arrivals = pipeline_orders[-min(3, len(pipeline_orders)):]
        demand_estimate = sum(recent_arrivals) / len(recent_arrivals)
    else:
        demand_estimate = 100.0  # Default estimate

    # Adjust base stock based on demand estimate
    adjusted_base = base_stock + demand_forecast_factor * (demand_estimate - 100.0)

    # Calculate raw order
    raw_order = max(0, adjusted_base + safety_stock - inventory_position)

    # Apply smoothing with pipeline consideration
    if pipeline_orders:
        # Consider pipeline stability in smoothing
        pipeline_variability = abs(pipeline_orders[-1] - raw_order) / max(1.0, raw_order)
        effective_smoothing = smoothing_factor * (1.0 + pipeline_weight * pipeline_variability)
        effective_smoothing = min(effective_smoothing, 0.8)

        order_amount = effective_smoothing * raw_order + (1 - effective_smoothing) * pipeline_orders[-1]
    else:
        order_amount = raw_order

    return order_amount
