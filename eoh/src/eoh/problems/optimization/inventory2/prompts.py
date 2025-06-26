class GetPrompts():
    def __init__(self):
        self.prompt_task = """
        Design a novel inventory management algorithm for a system with lost sales and lead time.
        Given historical demand data, pipeline inventory (orders in transit), and cost parameters, compute the optimal order amount each period to minimize total costs (holding + lost sales).
        Must differ from classical methods.
        """
        self.prompt_func_name = "compute_order_amount"
        self.prompt_func_inputs = [
            "current_inventory",
            "pipeline_inventory",
            "history_demand",
            "holding_cost",
            "lost_sales_cost",
            "lead_time"
        ]
        self.prompt_func_outputs = ["order_amount"]

        self.prompt_inout_inf = """
        Inputs:
        - `current_inventory` (float): On-hand inventory at the start of the period.
        - `pipeline_inventory` (list[float]): Orders in transit, indexed as [oldest → newest].
        - `history_demand` (list[float]): All historical demand values up to current period.
        - `holding_cost` (float): Cost to hold one unit of inventory for one period.
        - `lost_sales_cost` (float): Cost per unit of lost sales (demand not fulfilled).
        - `lead_time` (int): Fixed delay between order placement and arrival.

        Output:
        - `order_amount` (float): Units to order this period (≥0).
        """

        self.prompt_other_inf = """
        `pipeline_inventory` is a FIFO queue of length `lead_time`, where:
             - `pipeline_inventory[0]`: Order placed `lead_time` periods ago (arriving next).
             - `pipeline_inventory[-1]`: Order placed 1 period ago (arriving in `lead_time` periods).
        """

    def get_task(self):
        return self.prompt_task
    
    def get_func_name(self):
        return self.prompt_func_name
    
    def get_func_inputs(self):
        return self.prompt_func_inputs
    
    def get_func_outputs(self):
        return self.prompt_func_outputs
    
    def get_inout_inf(self):
        return self.prompt_inout_inf

    def get_other_inf(self):
        return self.prompt_other_inf

