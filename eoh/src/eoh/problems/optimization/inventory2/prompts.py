class GetPrompts():
    def __init__(self, prompt_version='v2'):
        self.version = prompt_version  # 'v1' = old version, 'v2' = new version

        if self.version == 'v1':
            self._init_v1()
        else:  # v2 is default
            self._init_v2()

    def _init_v1(self):
        """Old version (m1_20251009_155357.txt style)"""
        self.prompt_task = r"""
        We consider the problem of controlling the inventory of a product over $T$ periods faced by a manager.
        At the beginning of period $t=1,2,\dots, T$, the manager knows the following information:
        (i) the on-hand inventory denoted by $I_{t}$, which is a non-negative number, and
        (ii) the pipeline orders, denoted $Q_{t} = (q_{t,1}, q_{t,2}, \dots, q_{t,L})$, where $q_{t,k}$ captures
        the amount of the product that will arrive at the beginning of $t+k-1$ period. Here, the constant $L$, which is known to the
        manager, denotes the lead time. Upon observing the on-hand inventory and pipeline orders, the manager
        places an order of size $a_t \geq 0$, which will arrive after $L$ periods. After the order is placed,
        the manager faces the uncertain demand of $D_t$. At the end of time $t$, the manager observes the sales
        amount of $S_{t} := \min(I_{t}, D_{t})$, encounters the lost sales of $L_{t} = \max(0, D_{t} - I_{t})$,
        and carries to the next period $\max(0, I_t - D_t)$ inventory. At the end of time $t$, the manager incurs
        (i) the holding cost of $h \times \max(0, I_t - D_t)$, where $h$ is a fixed holding cost known to the
        manager, and (ii) the lost-sales cost of $p \times \max(0, D_t - I_t)$, where $p$ is a fixed lost-sales
        cost known to the manager. Thus, the manager incurs the immediate cost of
        $c(I_t, D_t) = h \cdot \max(0, I_t - D_t) \;+\; p \cdot \max(0, D_t - I_t)$ at the end of each period $t$,
        which is the summation of holding cost and lost-sales cost. Transitioning to period $t+1$, the on-hand
        inventory level becomes updated to $I_{t+1} = \max(0, I_t - D_t)$, and the pipeline orders becomes
        updated to $Q_{t+1} = (q_{t,2}, \dots, q_{t,L}, a_t)$. The manager's ultimate goal is to find a heuristic
        policy, denoted $\pi$, that results in low costs. The policy $\pi$ is given by the sequence of decision
        rules $(\pi_1,\pi_2,\dots,\pi_T)$, where the decision rule at time $t$, which is $\pi_t$, receives as
        input the on-hand inventory and pipeline orders and returns an order of size. Specifically, the manager
        accesses $N$ training demand trajectories of length $T$ with the vectorized form of
        $(D_{1}^n, D_{2}^n,\dots, D_{T}^n)$ for $n=1,2,\dots, N$. The manager's objective is thus to find the
        best policy $\pi=(\pi_1,\pi_2,\dots,\pi_T)$ that minimizes the average cumulative costs. That is, to
        find an optimal policy that minimizes the following empirical optimization problem:
        \[
        \min_{\pi} \frac{1}{N}\sum_{n=1}^N\sum_{t=1}^T c(I^{\pi,n}_t, D_t^n),
        \]
        where $I^{\pi,n}_t$ is the on-hand inventory level at time $t$ if the manager follows policy
        $\pi=(\pi_1,\pi_2,\dots,\pi_T)$ on the demand trajectory $n$.

        The dynamics of each period can be described with the following pseudocode:

        ```python
        for t in range(T):
            # 1. Arrival
            I_t += Q_t[0]

            # 2. Order placement
            a_t = policy(I_t, Q_t)

            # 3. Demand realization and cost
            D_t = demand[t]
            holding_cost_t    = h * max(0, I_t - D_t)
            lost_sales_cost_t = p * max(0, D_t - I_t)
            c_t = holding_cost_t + lost_sales_cost_t

            # 4. State transition
            I_t = max(0, I_t - D_t)
            Q_t = Q_t[1:] + [a_t]
        ```

        Given the demand distribution is unknown, you are provided with historical demand data. Your task is to
        improve a given policy to generate an implementation that minimizes total costs
        on the training data.
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

    def _init_v2(self):
        """New version with improved notation"""
        self.prompt_task = r"""
        We consider the problem of controlling the inventory of a product over $T$ discrete periods faced by a manager. 
        At the beginning of each period $t = 1, 2, \dots, T$, the manager observes the on-hand inventory $I_t \ge 0$, 
        representing the stock available at the end of the previous period, and the pipeline orders 
        $Q_t = (q_{t,1}, q_{t,2}, \dots, q_{t,L})$, where $q_{t,k}$ denotes the quantity of product scheduled to arrive at the beginning of period $t+k-1$. 
        The lead time $L$ is fixed and known to the manager.

        At the beginning of period $t$, the order $q_{t,1}$ arrives. Thus, before meeting the demand, 
        the manager has a total of $I_t + q_{t,1}$ units available for sales. After observing the state $(I_t, Q_t)$, 
        the manager places a new replenishment order $a_t \ge 0$, which will arrive after $L$ periods.

        Then, the random demand $D_t$ is realized. We define the sales and lost sales quantities by explicitly separating the on-hand and arriving inventory:
        \[
        S_t = \min(I_t + q_{t,1},\, D_t),
        \qquad
        L_t = \max(0,\, D_t - I_t - q_{t,1}).
        \]
        The leftover inventory that carries over to the next period is 
        \[
        I_{t+1} = \max(0,\, I_t + q_{t,1} - D_t),
        \]
        and the pipeline orders transition as follows. 
        After $q_{t,1}$ arrives at the beginning of period $t$ and the manager places a new order $a_t$, 
        each remaining order moves one step closer to arrival. 
        Hence, the pipeline at the beginning of $t+1$ is
        \[
        Q_{t+1} = (q_{t,2}, q_{t,3}, \dots, q_{t,L}, a_t).
        \]

        During each period $t$, the manager incurs an immediate holding cost of $h \times \max(0,\, I_t + q_{t,1} - D_t)$ for leftover inventory 
        and an immediate lost-sales cost of $p \times \max(0,\, D_t - I_t - q_{t,1})$ for unmet demand, where $h$ is a fixed holding cost per unit per period and $p$ is a fixed lost-sales cost per unit known to the manager.
        Hence, the immediate total cost in period $t$ is the sum of the immediate holding cost and immediate lost-sales cost
        \[
        c(I_t, q_{t,1}, D_t) 
        = h \cdot \max(0,\, I_t + q_{t,1} - D_t)
        + p \cdot \max(0,\, D_t - I_t - q_{t,1}).
        \]

        The manager seeks a stationary policy $\pi$ that maps the observed state $(I_t, Q_t)$ to an order quantity $a_t = \pi(I_t, Q_t)$. Given $N$ historical demand trajectories $(D_1^n, D_2^n, \dots, D_T^n)$ for $n = 1, 2, \dots, N$, 
        the objective is to find a stationary policy that minimizes the average cumulative total cost. That is, to find an optimal policy that minimizes the following empirical optimization problem:
        \[
        \min_{\pi} \frac{1}{N}\sum_{n=1}^N\sum_{t=1}^T 
        c\big(I_t^{\pi,n}, q_{t,1}^{\,\pi,n}, D_t^n\big),
        \]
        where $I_t^{\pi,n}$ and $q_{t,1}^{\,\pi,n}$ denote, respectively, the on-hand inventory and the arriving order under the stationary policy $\pi$ along demand trajectory $n$.


        The dynamics can be described with the following pseudocode:

        Initialize average_cumulative_total_cost = 0

        For each demand trajectory n = 1, 2, …, N:
            Set I_1 = initial_inventory
            Set Q_1 = (0, 0, …, 0)   # length L

            For each period t = 1, 2, …, T:
                # 1. Arrival of oldest pipeline order
                q_{t,1} = first element of Q_t

                # 2. Order placement
                a_t = policy(I_t, Q_t)

                # 3. Demand realization
                D_t = D_t^n

                # 4. Immediate cost calculation
                c(I_t, q_{t,1}, D_t)
                    = h * max(0, I_t + q_{t,1} - D_t)
                    + p * max(0, D_t - I_t - q_{t,1})

                Add c(I_t, q_{t,1}, D_t) to average_cumulative_total_cost

                # 5. State transition to next period
                I_{t+1} = max(0, I_t + q_{t,1} - D_t)
                Q_{t+1} = (q_{t,2}, q_{t,3}, …, q_{t,L}, a_t)

        Compute:
            average_cumulative_total_cost = (1 / N) * average_cumulative_total_cost

        Return average_cumulative_total_cost

        """
        self.prompt_func_name = "compute_order_amount"
        self.prompt_func_inputs = [
            "on_hand_inventory",
            "pipeline_orders",
        ]
        self.prompt_func_outputs = ["order_amount"]

        self.prompt_inout_inf = r"""
        Inputs:
        - `on_hand_inventory` (float): On-hand inventory $I_t$ at the start of current period.
        - `pipeline_orders` (list[float]): Pipeline orders $Q_t = (q_{t,1}, q_{t,2}, \ldots, q_{t,L})$, indexed as [oldest → newest].

        Output:
        - `order_amount` (int): Order quantity $a_t$ for this period (≥0).
        """

        self.prompt_other_inf = """
        Note: `pipeline_orders` is a FIFO queue of length $L$ (lead time), where:
             - `pipeline_orders[0]` = $q_{t,1}$: Order placed $L$ periods ago (arriving at the beginning of period $t$).
             - `pipeline_orders[-1]` = $q_{t,L}$: Order placed 1 period ago (arriving in $L$ periods).
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

