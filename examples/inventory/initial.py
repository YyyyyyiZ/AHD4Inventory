def base_stock(history_demand, history_inventory, history_lost, holding_cost, lost_sales_cost):
    """
    Base Stock Policy
    """
    base_stock = 160
    order_amount = max(0, base_stock - history_inventory[-1])
    return order_amount



def constant_order(history_demand, history_inventory, history_lost, holding_cost, lost_sales_cost):
    """
    Constant Order Policy
    """
    t = len(history_inventory)-1
    interval = 2
    if t%interval:
        order_amount = 0
    else:
        order_amount = 100

    return order_amount


def capped_base_stock(history_demand, history_inventory, history_lost, holding_cost, lost_sales_cost):
    """
    Capped Base Stock Policy
    """
    base_stock = 70
    order_cap = 30

    order_amount = min(base_stock - history_inventory[-1], order_cap)
    return order_amount