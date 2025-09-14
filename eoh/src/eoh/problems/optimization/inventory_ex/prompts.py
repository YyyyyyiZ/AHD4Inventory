class GetPrompts():
    def __init__(self):
        self.prompt_task = """
        Consider an inventory system with lost sales and positive lead time. 
        You are given a policy that computes the order quantity each period to minimize total costs (holding and lost sales), based on the current inventory and pipeline inventory (orders in transit).
        Your task is to adjust the parameters of this policy to generate an improved implementation.
        """
        self.prompt_func_name = "compute_order_amount"
        self.prompt_func_inputs = [
            "current_inventory",
            "pipeline_inventory",
        ]
        self.prompt_func_outputs = ["order_amount"]

        self.prompt_inout_inf = """
        Inputs:
        - `current_inventory` (float): On-hand inventory at the current period.
        - `pipeline_inventory` (list[float]): Orders in transit, indexed as [oldest → newest].

        Output:
        - `order_amount` (int): Units to order this period (≥0).
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

