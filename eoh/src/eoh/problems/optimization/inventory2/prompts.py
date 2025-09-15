class GetPrompts():
    def __init__(self):
        self.prompt_task = r"""
        Consider an inventory system with lost sales and positive lead time $L$. Formally,
        State $(I_t, Q_t)$ with $I_t$ on-hand inventory and $Q_t=(q_{t,1},\dots,q_{t,L})$ pipeline orders.
        Decision $a_t \ge 0$ (order amount).
        Demand $D_t \sim \mathbb{P}(\cdot \mid \text{history})$.
        Dynamics: \[ I_{t+1} = (I_t - D_t)_{+} + q_{t,1}, \quad Q_{t+1} = (q_{t,2}, \dots, q_{t,L}, a_t). \] 
        Cost: \[ C_t = h (I_t - D_t)_{+} + p (D_t - I_t)_{+}. \] 
        Objective: \[ \min_{\{a_t\}_{t\ge0}} \; \mathbb{E}\!\left[ \sum_{t=0}^T C_t \right]. \]  
        
        Given historical demand data, pipeline inventory (orders in transit), and cost parameters, compute the optimal order amount each period to minimize total costs (holding + lost sales).
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
        - `current_inventory` (float): On-hand inventory at the start of operation.
        - `pipeline_inventory` (list[float]): Orders in transit, indexed as [oldest → newest].
        - `history_demand` (list[float]): All historical demand values up to current period.
        - `holding_cost` (float): Cost to hold one unit of inventory for one period.
        - `lost_sales_cost` (float): Cost per unit of lost sales.
        - `lead_time` (int): Fixed delay between order placement and arrival.

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

