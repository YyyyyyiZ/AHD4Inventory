# sample_id: 081
# folder: deepseek-chat_poisson_L6_c1_2_50_plain_processed_scipy_15_default_m2_10_r4
# distribution: poisson_L6_c1_2
# generation: 2
# rank_in_population_file: 3
# objective: 2556.99901
# test_objective: 2552.16349
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;partial_adjustment
# extra_motifs: safety_stock_buffer
def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 665.8919289780819  # OPT_PARAM: {"initial": 665.8919289780819, "min": 10, "max": 1000, "type": "float"}
    safety_stock = 51.902379739927916  # OPT_PARAM: {"initial": 51.902379739927916, "min": 0, "max": 200, "type": "float"}
    smoothing_factor = 0.5093579167278066  # OPT_PARAM: {"initial": 0.5093579167278066, "min": 0, "max": 1, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Smooth adjustment to avoid extreme order fluctuations
    target_position = base_stock + safety_stock
    adjustment = smoothing_factor * (target_position - inventory_position)
    
    # Ensure non-negative order
    order_amount = max(0, adjustment)
    
    # Round to nearest integer (since order amounts should be integers)
    return order_amount
