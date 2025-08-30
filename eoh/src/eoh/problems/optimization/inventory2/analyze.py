import numpy as np


class InventoryAnalyzer:
    def __init__(self, prob, n_train, data_summary=None, algo_performance='no', param_info=None):
        self.prob = prob
        self.n_train = n_train
        self.data_summary = data_summary
        self.algo_performance = algo_performance
        self.param_info = param_info
        self.param = self.get_param_info()

    def get_param_info(self):
        if self.param_info:
            one_instance = self.prob.load_instances(mode='train', n_traj=self.n_train)[0]
            lead_time = one_instance['lead_time']
            initial_inventory = one_instance['initial_inventory']
            holding_cost = one_instance['holding_cost']
            lost_sales_cost = one_instance['lost_sales_cost']
            param_info = (
                f"Below are some problem parameters: "
                f"lead_time={lead_time}, "
                f"initial_inventory={initial_inventory}, "
                f"holding_cost={holding_cost}, "
                f"lost_sales_cost={lost_sales_cost}. "
            )
            return param_info
        else:
            return ""

    def get_data(self):
        instances = self.prob.load_instances(mode='train', n_traj=self.n_train)
        data = []
        for idx, traj in enumerate(instances, start=1):
            trajectory_data = {
                "trajectory_id": f"trajectory_{idx}",
                "demand": traj["demand"],
            }
            data.append(trajectory_data)

        return data

    def get_data_summary(self, num_traj=5):
        if self.data_summary:
            instances = self.prob.load_instances(mode='train', n_traj=self.n_train)
            data = []
            all_demands = []

            for idx, traj in enumerate(instances, start=1):
                demand_array = np.array(traj["demand"])
                trajectory_data = {
                    "trajectory_id": f"trajectory_{idx}",
                    "demand": traj["demand"],
                }
                data.append(trajectory_data)
                all_demands.append(demand_array)

            # Convert list of arrays into one big array
            all_demands = np.concatenate(all_demands)

            # Basic statistics
            mean_demand = np.mean(all_demands)
            std_demand = np.std(all_demands)
            min_demand = np.min(all_demands)
            max_demand = np.max(all_demands)
            cv_demand = std_demand / mean_demand if mean_demand != 0 else float("inf")

            # Per-trajectory stats (to see diversity)
            per_traj_stats = []
            for traj in data:
                arr = np.array(traj["demand"])
                per_traj_stats.append({
                    "id": traj["trajectory_id"],
                    "mean": np.mean(arr),
                    "std": np.std(arr),
                    "min": np.min(arr),
                    "max": np.max(arr)
                })

            # Construct text summary
            data_summary = []
            data_summary.append("Demand Data Summary (across all trajectories):")
            data_summary.append(f"- Total number of trajectories: {len(data)}")
            data_summary.append(f"- Total number of periods: {len(all_demands)}")
            data_summary.append(f"- Mean demand: {mean_demand:.2f}")
            data_summary.append(f"- Std deviation: {std_demand:.2f}")
            data_summary.append(f"- Min demand: {min_demand}, Max demand: {max_demand}")
            data_summary.append(f"- Coefficient of Variation (CV): {cv_demand:.2f}")

            data_summary.append("\nPer-trajectory statistics (mean ± std, min-max):")
            for stat in per_traj_stats[:num_traj]:  # show first num_traj for brevity
                data_summary.append(
                    f"  • {stat['id']}: mean={stat['mean']:.2f}, std={stat['std']:.2f}, "
                    f"range=({stat['min']}, {stat['max']})"
                )
            if len(per_traj_stats) > 5:
                data_summary.append(f"  ... and {len(per_traj_stats) - num_traj} more trajectories")

            return "\n".join(data_summary)
        else:
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
            cost_matrix = np.array(indiv["cost_matrix"])  # shape: [n_traj, n_periods, 2]  (holding, lost-sale)

            # Aggregate costs
            holding_costs = cost_matrix[:, :, 0]
            lostsale_costs = cost_matrix[:, :, 1]
            total_costs = holding_costs + lostsale_costs

            # Overall statistics
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
    - Average total cost per period: {mean_total:.2f} (std={std_total:.2f})
    - Average holding cost per period: {mean_holding:.2f}
    - Average lost-sale cost per period: {mean_lostsale:.2f}
    - Ratio holding : lost-sale = {mean_holding:.1f} : {mean_lostsale:.1f}
    - Per-trajectory total cost summary:
        mean={traj_mean:.2f}, std={traj_std:.2f}, range=({traj_min:.2f}, {traj_max:.2f})
            """)

        performance_summary_processed = "\n".join(summaries)
        return performance_summary_processed
