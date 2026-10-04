# sample_id: 083
# folder: deepseek-chat_normal_std30_L6_c1_2_50_plain_processed_scipy_15_default_e1-m2_6_r2
# distribution: normal_std30_L6_c1_2
# generation: 9
# rank_in_population_file: 3
# objective: 2398.26
# test_objective: 2414.279
# is_top10_by_distribution: False
# is_final_generation: False
# table_motifs: inventory_position;pipeline_weighting;nonlinear_pipeline_composition;order_up_to;partial_adjustment
# extra_motifs: integer_rounding;nonlinear_gap_transform
def compute_order_amount(on_hand_inventory, pipeline_orders):
    # Core base stock level
    base_stock = 541.0430695860339  # OPT_PARAM: {"initial": 541.0430695860339, "min": 300, "max": 900, "type": "float"}
    
    # Cost-ratio adjustment factor (p/h = 2)
    cost_ratio_factor = 1.377841154054285  # OPT_PARAM: {"initial": 1.377841154054285, "min": 1.0, "max": 3.0, "type": "float"}
    
    # Pipeline variability adjustment
    variability_threshold = 0.3961856822731612  # OPT_PARAM: {"initial": 0.3961856822731612, "min": 0.1, "max": 0.5, "type": "float"}
    variability_multiplier = 1.109110084850649  # OPT_PARAM: {"initial": 1.109110084850649, "min": 1.0, "max": 3.0, "type": "float"}
    
    # Order smoothing parameters
    smoothing_base = 0.115182788573315  # OPT_PARAM: {"initial": 0.115182788573315, "min": 0.1, "max": 0.8, "type": "float"}
    smoothing_adjust = 0.3  # OPT_PARAM: {"initial": 0.3, "min": 0.05, "max": 0.3, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate pipeline variability (new structural element)
    if len(pipeline_orders) > 1:
        pipeline_mean = sum(pipeline_orders) / len(pipeline_orders)
        pipeline_variance = sum((q - pipeline_mean) ** 2 for q in pipeline_orders) / len(pipeline_orders)
        variability_ratio = pipeline_variance / (pipeline_mean + 1e-6)
    else:
        variability_ratio = 0.0
    
    # Adjust base stock based on cost ratio and pipeline variability
    adjusted_base = base_stock * cost_ratio_factor
    if variability_ratio > variability_threshold:
        adjusted_base *= variability_multiplier
    
    # Calculate order-up-to gap
    order_gap = max(0, adjusted_base - inventory_position)
    
    # Dynamic smoothing based on gap size (new structural element)
    if order_gap > 0:
        gap_ratio = order_gap / (adjusted_base + 1e-6)
        dynamic_smoothing = smoothing_base + smoothing_adjust * (1.0 - gap_ratio)
        order_amount = max(0, int(round(dynamic_smoothing * order_gap)))
    else:
        order_amount = 0
    
    return order_amount
