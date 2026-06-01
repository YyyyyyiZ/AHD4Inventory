# sample_id: 080
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_m2plural_4_r7
# distribution: normal_std30_L6_c1_2
# generation: 1
# rank_in_population_file: 7
# objective: 4247.42
# test_objective: 4226.674
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;state_dependent_target
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy;near_term_pipeline_focus;integer_rounding
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 571.8118933345869  # OPT_PARAM: {"initial": 571.8118933345869, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 26.823248836796438  # OPT_PARAM: {"initial": 26.823248836796438, "min": 0, "max": 200, "type": "float"}
    demand_adjustment_factor = 0.1  # OPT_PARAM: {"initial": 0.1, "min": 0.1, "max": 2.0, "type": "float"}
    
    # Estimate upcoming demand based on pipeline arrivals
    upcoming_arrivals = sum(pipeline_orders)
    
    # Calculate net inventory position
    net_inventory = on_hand_inventory + upcoming_arrivals
    
    # Adjust base stock based on recent pipeline pattern
    recent_orders = pipeline_orders[-3:] if len(pipeline_orders) >= 3 else pipeline_orders
    avg_recent = sum(recent_orders) / len(recent_orders) if recent_orders else 0
    
    # Dynamic adjustment: if recent orders are high, anticipate higher future demand
    dynamic_adjustment = avg_recent * demand_adjustment_factor
    
    # Calculate target inventory position
    target_inventory = base_stock + safety_stock + dynamic_adjustment
    
    # Calculate order amount
    order_amount = max(0, target_inventory - net_inventory)
    
    # Round to nearest integer (as order amounts should be integers)
    order_amount = int(round(order_amount))
    
    return order_amount
