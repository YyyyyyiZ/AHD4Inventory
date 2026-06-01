# sample_id: 008
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_4_r1
# distribution: poisson_L6_c1_2
# generation: 5
# rank_in_population_file: 8
# objective: 974.63576
# test_objective: 939.0302
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;state_dependent_target;partial_adjustment;order_clipping
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 510.93467142866245  # OPT_PARAM: {"initial": 510.93467142866245, "min": 400, "max": 700, "type": "float"}
    safety_stock = 45.0  # OPT_PARAM: {"initial": 45.0, "min": 20, "max": 80, "type": "float"}
    demand_estimate = 97.75006872229582  # OPT_PARAM: {"initial": 97.75006872229582, "min": 90, "max": 110, "type": "float"}
    smoothing_factor = 0.05  # OPT_PARAM: {"initial": 0.05, "min": 0.05, "max": 0.3, "type": "float"}
    pipeline_weight = 0.5  # OPT_PARAM: {"initial": 0.5, "min": 0.1, "max": 0.5, "type": "float"}
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected demand during lead time
    expected_lead_time_demand = demand_estimate * len(pipeline_orders)
    
    # Calculate target inventory position
    target_position = expected_lead_time_demand + safety_stock
    
    # Calculate base order amount using (s,S) logic
    base_order = max(0, target_position - net_inventory)
    
    # Apply base stock ceiling
    max_order = max(0, base_stock - net_inventory)
    
    # Adjust for pipeline coverage (reduce order if pipeline is already high)
    pipeline_coverage = sum(pipeline_orders) / max(1, expected_lead_time_demand)
    pipeline_adjustment = 1.0 - pipeline_weight * min(1.0, pipeline_coverage)
    
    # Calculate adjusted order
    adjusted_order = min(base_order, max_order) * pipeline_adjustment
    
    # Smooth with demand estimate to prevent extreme orders
    order_amount = smoothing_factor * adjusted_order + (1 - smoothing_factor) * demand_estimate
    
    # Round to nearest integer
    return order_amount
