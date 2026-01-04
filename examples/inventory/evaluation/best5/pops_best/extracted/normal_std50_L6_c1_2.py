# Auto-extracted policy code
# Source JSON: normal_std50_L6_c1_2.json
# Extracted at: 2026-01-04 09:19:33

def compute_order_amount(on_hand_inventory, pipeline_orders):
    base_stock = 446.4815808764805  # OPT_PARAM: {"initial": 446.4815808764805, "min": 400, "max": 500, "type": "float"}
    safety_stock = 96.4815808764795  # OPT_PARAM: {"initial": 96.4815808764795, "min": 80, "max": 120, "type": "float"}
    demand_forecast_factor = 0.37959154685032287  # OPT_PARAM: {"initial": 0.37959154685032287, "min": 0.1, "max": 0.5, "type": "float"}
    smoothing_factor = 0.11203194875511265  # OPT_PARAM: {"initial": 0.11203194875511265, "min": 0.1, "max": 0.3, "type": "float"}
    
    # Calculate inventory position
    inventory_position = on_hand_inventory + sum(pipeline_orders)
    
    # Calculate simple pipeline average (more stable than weighted)
    if len(pipeline_orders) > 0:
        pipeline_avg = sum(pipeline_orders) / len(pipeline_orders)
    else:
        pipeline_avg = 0
    
    # Adjust base stock based on pipeline average
    adjusted_base_stock = base_stock + demand_forecast_factor * pipeline_avg
    
    # Calculate order-up-to level
    order_up_to = adjusted_base_stock + safety_stock
    
    # Order amount is the difference between order-up-to level and inventory position
    order_amount = max(0, order_up_to - inventory_position)
    
    # Apply smoothing using pipeline average
    smoothed_order = smoothing_factor * order_amount + (1 - smoothing_factor) * pipeline_avg
    order_amount = max(0, smoothed_order)
    
    # Round to nearest integer
    order_amount = int(round(order_amount))
    
    return order_amount
