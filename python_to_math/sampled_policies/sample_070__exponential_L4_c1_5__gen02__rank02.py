# sample_id: 070
# folder: deepseek-chat_exponential_L4_c1_5_50_plain_processed_scipy_15_default_m2_10_r1
# distribution: exponential_L4_c1_5
# generation: 2
# rank_in_population_file: 2
# objective: 11182.29596
# test_objective: 11335.45953
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;order_up_to;partial_adjustment
# extra_motifs: safety_stock_buffer;pipeline_demand_proxy
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 427.05501776950115  # OPT_PARAM: {"initial": 427.05501776950115, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 34.79592594200072  # OPT_PARAM: {"initial": 34.79592594200072, "min": 0, "max": 300, "type": "float"}
    demand_estimate = 84.78492538308028  # OPT_PARAM: {"initial": 84.78492538308028, "min": 50, "max": 400, "type": "float"}
    adjustment_factor = 0.25047133377839226  # OPT_PARAM: {"initial": 0.25047133377839226, "min": 0.1, "max": 1.5, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate expected shortfall considering pipeline
    expected_shortfall = max(0, base_stock - inventory_position)
    
    # Adjust for demand variability with safety stock
    adjusted_shortfall = expected_shortfall * adjustment_factor + safety_stock
    
    # Consider upcoming demand in pipeline
    upcoming_demand_estimate = demand_estimate * len(pipeline_orders)
    pipeline_adjustment = max(0, upcoming_demand_estimate - sum(pipeline_orders)) * 0.3
    
    # Final order amount
    order_amount = max(0, adjusted_shortfall + pipeline_adjustment)
    
    return order_amount
