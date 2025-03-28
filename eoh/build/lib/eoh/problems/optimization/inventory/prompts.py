class GetPrompts():
    def __init__(self):
        self.prompt_task = """
                Design a novel inventory management algorithm for a system with:
                - Lost sales
                - Lead time = 1 period
                Given historical data and cost parameters, compute the optimal order amount each period to minimize total costs (holding + lost sales).

                Key Requirements:
                1. Must differ from existing literature approaches
                2. Balance inventory holding costs vs lost sales costs
                3. Consider lead time in ordering decisions
                4. The decision made in current period cannot depend on future demand realizations

                Approach:
                1. Analyze demand patterns from history
                2. Develop adaptive ordering strategy
                3. Incorporate real-time inventory adjustments
                4. Optimize for both current and anticipated costs
                """
        self.prompt_func_name = "compute_order_amount"
        self.prompt_func_inputs = ["history_demand", "history_inventory", "history_lost", "holding_cost",
                                   "lost_sales_cost"]
        self.prompt_func_outputs = ["order_amount"]
        self.prompt_inout_inf = """
                'history_demand': List of demand quantities per period,
                'history_inventory': List of ending inventory levels per period,
                'history_lost': List of lost sales quantities per period,
                'holding_cost': Cost per unit per period (float),
                'lost_sales_cost': Cost per unit of lost sales (float).
                """
        self.prompt_other_inf = "'history_demand', 'history_inventory' and 'history_lost' are Lists. 'holding_cost' and 'lost_sales_cost' are floats."


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

