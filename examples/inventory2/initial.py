def base_stock(current_inventory, pipeline_inventory, history_demand, holding_cost, lost_sales_cost, lead_time):
    """
    Base Stock Policy
    """
    base_stock = 160
    order_amount = max(0, base_stock - current_inventory)
    return order_amount



def constant_order(current_inventory, pipeline_inventory, history_demand, holding_cost, lost_sales_cost, lead_time):
    """
    Constant Order Policy
    """
    t = len(history_demand)-1
    interval = 2
    if t%interval:
        order_amount = 0
    else:
        order_amount = 100

    return order_amount


def capped_base_stock(current_inventory, pipeline_inventory, history_demand, holding_cost, lost_sales_cost, lead_time):
    """
    Capped Base Stock Policy
    """
    base_stock = 70
    order_cap = 30

    order_amount = min(base_stock - current_inventory, order_cap)
    return order_amount