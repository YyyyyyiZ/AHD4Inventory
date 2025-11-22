import numpy as np


class InventoryAnalyzer:
    def __init__(self, prob, n_train, data_summary='no', algo_performance='no', param_info=None, prompt_version='v2'):
        self.prob = prob
        self.n_train = n_train
        self.data_summary = data_summary
        self.algo_performance = algo_performance
        self.param_info = param_info
        self.version = prompt_version  # 'v1' = old version, 'v2' = new version
        self.param = self.get_param_info()

    def get_param_info(self):
        if self.param_info:
            one_instance = self.prob.load_instances(mode='train', n_traj=self.n_train)[0]
            lead_time = one_instance['lead_time']
            initial_inventory = one_instance['initial_inventory']
            holding_cost = one_instance['holding_cost']
            lost_sales_cost = one_instance['lost_sales_cost']

            # Get selling horizon T (number of periods excluding planning phase)
            # The demand length minus lead_time gives us the selling horizon
            selling_horizon = len(one_instance['demand']) - lead_time

            if self.version == 'v1':
                param_info = (
                    f"Below are some problem parameters: "
                    f"lead_time $L$ ={lead_time}, "
                    f"initial_inventory $I_0$ ={initial_inventory}, "
                    f"holding_cost $h$ ={holding_cost}, "
                    f"lost_sales_cost $p$ ={lost_sales_cost}. "
                )
            else:  # v2
                param_info = (
                    f"Below are some problem parameters:\n"
                    f"- Selling phase horizon: $T$ = {selling_horizon} periods\n"
                    f"- Lead time: $L$ = {lead_time} periods\n"
                    f"- Holding cost: $h$ = {holding_cost} per unit per period\n"
                    f"- Lost-sales cost: $p$ = {lost_sales_cost} per unit\n"
                )
            return param_info
        else:
            return ""

    def get_data_summary(self, num_traj=5):
        if self.data_summary == 'processed':
            instances = self.prob.load_instances(mode='train', n_traj=self.n_train)
            all_demands = []

            for idx, traj in enumerate(instances, start=1):
                demand_array = np.array(traj["demand"])
                all_demands.extend(demand_array)

            # Convert to numpy array for calculations
            all_demands_array = np.array(all_demands)

            # Basic statistics
            mean_demand = np.mean(all_demands_array)
            std_demand = np.std(all_demands_array)
            min_demand = np.min(all_demands_array)
            max_demand = np.max(all_demands_array)
            cv_demand = std_demand / mean_demand if mean_demand != 0 else float("inf")

            # Calculate quantiles (10, 20, ..., 90)
            quantiles = [10, 20, 30, 40, 50, 60, 70, 80, 90]
            demand_quantiles = np.percentile(all_demands_array, quantiles)

            # Construct text summary
            data_summary = []
            data_summary.append("Demand Data Summary (across all trajectories):")
            data_summary.append(f"- Total number of trajectories: {len(instances)}")
            data_summary.append(f"- Total number of periods: {len(all_demands_array)}")
            data_summary.append(f"- Mean demand: {mean_demand:.2f}")
            data_summary.append(f"- Std deviation: {std_demand:.2f}")
            data_summary.append(f"- Min demand: {min_demand}, Max demand: {max_demand}")
            data_summary.append(f"- Coefficient of Variation (CV): {cv_demand:.2f}")
            data_summary.append(f"- Demand quantiles (10-90%): {[f'{q:.1f}' for q in demand_quantiles]}")

            return "\n".join(data_summary)
        elif self.data_summary == 'plain':
            instances = self.prob.load_instances(mode='train', n_traj=self.n_train)
            demand_text = ''
            for idx, traj in enumerate(instances, start=1):
                if self.version == 'v1':
                    demand_text += f"Trajectory {idx} demand sequence: {traj['demand']}\n"
                    demand_text += f"Trajectory {idx} demand sequence: {traj['demand'][traj['lead_time']:]}\n"
                else:  # v2
                    demand_text += f"Historical demand trajectory $D^{{{idx}}}$: {traj['demand']}\n"
                    # demand_text += f"Historical demand trajectory $D^{{{idx}}}$: {traj['demand'][traj['lead_time']:]}\n"
            return demand_text
        else:   # self.data_summary == 'no'
            return None

    def get_algo_performance(self, indivs):
        if self.algo_performance == 'plain':
            return self._get_plain(indivs, n_sample=3)
        elif self.algo_performance == 'processed':
            return self._get_processed(indivs)
        else:
            return None

    def _get_plain(self, indivs, n_sample):
        summaries = []
        for i, indiv in enumerate(indivs, start=1):
            order_matrix = np.array(indiv["order_matrix"])  # shape: [n_traj, n_periods]
            cost_matrix = np.array(indiv["cost_matrix"])  # shape: [n_traj, n_periods, 2]
            n_traj, n_periods = order_matrix.shape
            # Compute total cost per trajectory
            traj_total_cost = np.sum(cost_matrix[:, :, 0] + cost_matrix[:, :, 1], axis=1)

            # Select representative trajectories: min, median, max cost
            sorted_indices = np.argsort(traj_total_cost)
            selected_indices = [sorted_indices[0],  # best (min cost)
                                sorted_indices[len(sorted_indices) // 2],  # median
                                sorted_indices[-1]  # worst (max cost)
                                ][:n_sample]  # trim if fewer than 3 samples requested

            summary = [f"\nNo.{i} algorithm:"]
            summary.append(f"- Total trajectories: {n_traj}, periods per trajectory: {n_periods}")
            summary.append("- Below are sampled trajectories (row = trajectory, col = period):")
            summary.append("  order_matrix entries = order amount per period")
            summary.append("  cost_matrix entries = (holding_cost, lost_sale_cost) per period\n")

            for idx in selected_indices:
                orders = order_matrix[idx]
                costs = cost_matrix[idx]
                total_cost = traj_total_cost[idx]

                summary.append(f"    Trajectory {idx + 1} (total cost={total_cost:.2f}):")
                summary.append(f"    Orders: {orders.tolist()}")
                summary.append(f"    Costs: {costs.tolist()}")  # list of tuples per period
            summaries.append("\n".join(summary))
        performance_summary_plain = "\n".join(summaries)
        return performance_summary_plain

    def _get_processed(self, indivs):
        summaries = []

        for i, indiv in enumerate(indivs, start=1):
            order_matrix = np.array(indiv["order_matrix"])  # shape: [n_traj, n_periods]
            cost_matrix = np.array(indiv["cost_matrix"])  # shape: [n_traj, n_periods, 2]  (holding, lost-sales)

            # Aggregate costs
            holding_costs = cost_matrix[:, :, 0]
            lostsale_costs = cost_matrix[:, :, 1]
            total_costs = holding_costs + lostsale_costs

            if self.version == 'v1':
                # Old version: per-period statistics
                mean_total = np.mean(total_costs)
                std_total = np.std(total_costs)
                mean_holding = np.mean(holding_costs)
                mean_lostsale = np.mean(lostsale_costs)

                # Per-trajectory robustness analysis
                traj_total = np.sum(total_costs, axis=1)  # total cost per trajectory
                traj_mean = np.mean(traj_total)
                traj_std = np.std(traj_total)
                traj_min = np.min(traj_total)
                traj_max = np.max(traj_total)

                summaries.append(f"""
    No.{i} algorithm:
    - Average total cost per period = {mean_total:.2f} (std={std_total:.2f})
    - Average holding cost per period = {mean_holding:.2f}
    - Average lost-sale cost per period = {mean_lostsale:.2f}
    - Ratio holding : lost-sale = {mean_holding:.1f} : {mean_lostsale:.1f}
    - Per-trajectory total cost summary: mean = {traj_mean:.2f}, std={traj_std:.2f}, range=({traj_min:.2f}, {traj_max:.2f})
            """)
            else:  # v2
                # New version: per-period statistics (same as v1 but with "policy" label)
                mean_total = np.mean(total_costs)
                std_total = np.std(total_costs)
                mean_holding = np.mean(holding_costs)
                mean_lostsale = np.mean(lostsale_costs)

                # Per-trajectory robustness analysis
                traj_total = np.sum(total_costs, axis=1)  # total cost per trajectory
                traj_mean = np.mean(traj_total)
                traj_std = np.std(traj_total)
                traj_min = np.min(traj_total)
                traj_max = np.max(traj_total)

                summaries.append(f"""
    No.{i} policy:
    - Average total cost per period:
      $\\frac{{1}}{{NT}} \\sum_{{n=1}}^N \\sum_{{t=L+1}}^{{L+T}} \\Big[ h \\cdot \\max(0,\\, I_t^{{\\pi,n}} + q_{{t,1}}^{{\\,\\pi,n}} - D_t^n) + p \\cdot \\max(0,\\, D_t^n - I_t^{{\\pi,n}} - q_{{t,1}}^{{\\,\\pi,n}}) \\Big]$ = {mean_total:.2f} (std={std_total:.2f})
    - Average holding cost per period:
      $\\frac{{1}}{{NT}} \\sum_{{n=1}}^N \\sum_{{t=L+1}}^{{L+T}} h \\cdot \\max(0,\\, I_t^{{\\pi,n}} + q_{{t,1}}^{{\\,\\pi,n}} - D_t^n)$ = {mean_holding:.2f}
    - Average lost-sales cost per period:
      $\\frac{{1}}{{NT}} \\sum_{{n=1}}^N \\sum_{{t=L+1}}^{{L+T}} p \\cdot \\max(0,\\, D_t^n - I_t^{{\\pi,n}} - q_{{t,1}}^{{\\,\\pi,n}})$ = {mean_lostsale:.2f}
    - Ratio holding : lost-sales = {mean_holding:.1f} : {mean_lostsale:.1f}
    - Per-trajectory total cost:
      $\\sum_{{t=L+1}}^{{L+T}} \\Big[ h \\cdot \\max(0,\\, I_t^{{\\pi,n}} + q_{{t,1}}^{{\\,\\pi,n}} - D_t^n) + p \\cdot \\max(0,\\, D_t^n - I_t^{{\\pi,n}} - q_{{t,1}}^{{\\,\\pi,n}}) \\Big]$
      mean = {traj_mean:.2f}, std={traj_std:.2f}, range=({traj_min:.2f}, {traj_max:.2f})
            """)

        performance_summary_processed = "\n".join(summaries)
        return performance_summary_processed
