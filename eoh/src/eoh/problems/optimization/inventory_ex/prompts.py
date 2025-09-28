class GetPrompts():
    def __init__(self):
        self.prompt_task = """
        We consider a single-product inventory system that operates in discrete periods $t=1,2,\dots,T$. 
        The system has positive lead time $L$ and lost sales.  

        At the beginning of period $t$, the state consists of:  
        - On-hand inventory $I_t \geq 0$.  
        - Pipeline orders $Q_t = (q_{t,1}, q_{t,2}, \dots, q_{t,L})$, where $q_{t,k}$ will arrive in $k$ periods.  

        The sequence of events in each period is:  
        1. Arrival: $I_t \leftarrow I_t + q_{t,1}$.  
        2. Order placement: a new replenishment order $a_t \geq 0$ is placed; it will arrive after $L$ periods.  
        3. Demand realization: random demand $D_t$ occurs. Sales and lost sales are
        \[
        S_t = \min(I_t, D_t), \quad 
        L_t = \max(0, D_t - I_t), \quad 
        I_{t+1} = \max(0, I_t - D_t).
        \]  
        4. Pipeline update:  
        \[
        Q_{t+1} = (q_{t,2}, \dots, q_{t,L}, a_t).
        \]  

        The cost in period $t$ is  
        \[
        c_t = h \cdot \max(0, I_t - D_t) \;+\; p \cdot \max(0, D_t - I_t).
        \]  

        The objective is  
        \[
        \min_{\{a_t \geq 0\}_{t=1}^T} \; \mathbb{E}\!\left[\sum_{t=1}^T c_t\right].
        \]  

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
        - `current_inventory` (float): On-hand inventory at the start of current period.
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

