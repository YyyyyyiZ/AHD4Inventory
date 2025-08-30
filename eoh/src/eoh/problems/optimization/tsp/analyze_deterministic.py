import numpy as np
from collections import Counter, defaultdict


class TSPAnalyzer:
    def __init__(self, prob, n_train, data_summary=None, algo_performance='no', summary_text=True, param_info=None):
        self.prob = prob
        self.n_train = n_train
        self.data_summary = data_summary
        self.algo_performance = algo_performance
        self.summary_text = summary_text
        self.param_info = param_info
        self.param = self.get_param_info()

    def get_param_info(self):
        return ""

    def get_data_summary(self, k_top=3, include_edge_stats=True, include_neighbor_stability=True,
                         include_global_stats=True):
        """
        Summarize the TSP *data* across scenarios.

        Parameters
        ----------
        scenarios : list of dict
            Each element is a scenario dict with:
              - 'coordinates': list[list[float, float]] (shared across all scenarios)
              - 'distances' : list[list[float]]         (noisy per scenario)
        k_top : int
            Top-K mean nearest neighbors reported per node (policy design aid).
        include_edge_stats : bool
            If True, compute per-edge mean/std/CV matrices.
        include_neighbor_stability : bool
            If True, compute how stable each node's nearest neighbor is across scenarios.
        include_global_stats : bool
            If True, compute overall edge length summary statistics.

        Returns
        -------
        summary_dict : dict
            Machine-friendly summary.
        summary_text : str or None
            Human-readable text (if summarize_text=True), otherwise None.
        """
        if self.data_summary:
            scenarios = self.prob.load_instances(mode='train', n_traj=self.n_train)

            # --- Basics ---
            n_scenarios = len(scenarios)
            coords = np.array(scenarios[0]['coordinates'])
            n_cities = len(coords)

            # stack all distance matrices into shape [S, N, N]
            D = np.stack([np.array(s['distances'], dtype=float) for s in scenarios], axis=0)  # (S, N, N)

            summary = {
                "n_scenarios": int(n_scenarios),
                "n_cities": int(n_cities),
            }

            text_lines = ["The distance matrix is stochastic. Below are the data summaries."]
            text_lines.append(f"- Number of scenarios: {n_scenarios}")
            text_lines.append(f"- Number of nodes in each scenario: {n_cities}")

            # --- Edge-level statistics across scenarios ---
            if include_edge_stats:
                mean_D = D.mean(axis=0)  # (N, N)
                std_D = D.std(axis=0)  # (N, N)
                with np.errstate(divide='ignore', invalid='ignore'):
                    cv_D = np.where(mean_D != 0, std_D / mean_D, 0.0)

                summary["edge_stats"] = {
                    "mean_distance_matrix": mean_D.tolist(),
                    "std_distance_matrix": std_D.tolist(),
                    "cv_distance_matrix": cv_D.tolist()
                }
            # --- Global edge statistics (distributional view) ---
            if include_global_stats:
                upper_mask = np.triu(np.ones((n_cities, n_cities), dtype=bool), k=1)
                all_edges = D[:, upper_mask]  # (S, E)
                all_edges_flat = all_edges.flatten()
                g_mean = float(np.mean(all_edges_flat))
                g_std = float(np.std(all_edges_flat))
                g_min = float(np.min(all_edges_flat))
                g_max = float(np.max(all_edges_flat))
                summary["global_edge_stats"] = {
                    "mean": g_mean,
                    "std": g_std,
                    "min": g_min,
                    "max": g_max
                }
                text_lines.append(f"- Global edge length mean={g_mean:.3f}, std={g_std:.3f}, "
                                  f"min={g_min:.3f}, max={g_max:.3f}")

            # --- Nearest-neighbor stability & Top-K mean neighbors per node ---
            if include_neighbor_stability or k_top > 0:
                # Per-scenario nearest neighbor for each node
                # argmin over j != i
                nn_counts = []  # list of Counter for each node
                nn_mode_prob = np.zeros(n_cities)  # stability: P(same NN) across scenarios
                topk_neighbors = {}  # top-k by *mean* distance

                # Precompute mean distances if needed
                mean_D = D.mean(axis=0) if include_edge_stats else D.mean(axis=0)

                for i in range(n_cities):
                    # nearest neighbor across scenarios
                    c = Counter()
                    for s in range(n_scenarios):
                        row = D[s, i, :].copy()
                        row[i] = np.inf  # exclude self
                        j = int(np.argmin(row))
                        c[j] += 1
                    nn_counts.append(c)
                    most_common_count = c.most_common(1)[0][1]
                    nn_mode_prob[i] = most_common_count / n_scenarios  # stability for node i

                    # top-k neighbors by mean distances
                    row_mean = mean_D[i, :].copy()
                    row_mean[i] = np.inf
                    order = np.argsort(row_mean)
                    topk_neighbors[i] = [int(idx) for idx in order[:k_top]]

                if include_neighbor_stability:
                    summary["nearest_neighbor_stability"] = {
                        "per_node_mode_probability": nn_mode_prob.tolist(),
                        "mean_mode_probability": float(nn_mode_prob.mean())
                    }
                    text_lines.append(f"- Nearest-neighbor stability (mean mode prob): "
                                      f"{nn_mode_prob.mean():.3f}")

                if k_top > 0:
                    summary["topk_mean_neighbors"] = {"k": int(k_top), "per_node_topk": topk_neighbors}
            return "\n".join(text_lines)
        else:
            return None

    def get_algo_performance(self, indivs):
        """
        Summarize algorithm performance depending on self.algo_performance mode.

        - 'plain': show sampled raw trajectories (visiting order + step costs).
        - 'processed': show aggregated statistics (mean/std/min/max route length).
        """
        if self.algo_performance == 'plain':
            return self._get_plain(indivs, n_sample=3)
        elif self.algo_performance == 'processed':
            summaries = ''
            for i, indiv in enumerate(indivs, start=1):
                summaries = f"\nAlgorithm {i}:\n"
                summaries += self._get_processed(indiv, )
            return summaries
        else:
            return None

    def _get_plain(self, indivs, n_sample=3):
        """
        Plain mode:
        Show a few representative routes (best/median/worst) with their orders and step costs.
        """
        summaries = []
        for i, indiv in enumerate(indivs, start=1):
            order_matrix = np.array(indiv["order_matrix"])
            cost_matrix = np.array(indiv["cost_matrix"])
            n_traj, n_steps = order_matrix.shape
            traj_total_cost = np.sum(cost_matrix, axis=1)

            sorted_indices = np.argsort(traj_total_cost)
            selected_indices = [sorted_indices[0], sorted_indices[len(sorted_indices) // 2], sorted_indices[-1]][
                               :n_sample]

            summary = [f"\nAlgorithm {i}:"]
            summary.append(f"- Total scenarios: {n_traj}, total nodes per scenario: {n_steps}")
            summary.append("- Representative scenarios (best, median, worst):")
            for idx in selected_indices:
                orders = order_matrix[idx]
                costs = cost_matrix[idx]
                total_cost = traj_total_cost[idx]
                summary.append(f"  • Scenario {idx + 1}: total length={total_cost:.2f}")
                summary.append(f"    Visiting order: {orders.tolist()}")
                summary.append(f"    Step costs: {costs.tolist()}")
            summaries.append("\n".join(summary))
        return "\n".join(summaries)

    def _get_processed(self, indiv, include_edge_usage=True, include_step_stats=True):
        """
        Summarize policy performance from evaluate() outputs.

        Parameters
        ----------
        indiv : dict
        include_edge_usage : bool
            If True, compute edge usage frequencies across all scenarios.
        include_step_stats : bool
            If True, compute per-step mean/std (helps diagnose early vs. late errors).

        Returns
        -------
        perf_dict : dict
        perf_text : str
        """
        routes = np.array(indiv["order_matrix"], dtype=int)  # (S, T)
        step_costs = np.array(indiv["cost_matrix"], dtype=float)  # (S, T)
        S, T = routes.shape

        totals = step_costs.sum(axis=1)
        mean_total = float(totals.mean())
        std_total = float(totals.std())
        min_total = float(totals.min())
        max_total = float(totals.max())

        perf = {
            "n_scenarios": int(S),
            "steps_per_route": int(T),
            "total_length_stats": {
                "mean": mean_total, "std": std_total, "min": min_total, "max": max_total
            }
        }

        text_lines = []
        text_lines.append("Algorithm Performance Summary")
        text_lines.append(f"- Scenarios: {S}, steps per route: {T}")
        text_lines.append(f"- Total route length: mean={mean_total:.3f}, std={std_total:.3f}, "
                          f"min={min_total:.3f}, max={max_total:.3f}")

        # Edge usage frequency (how often policy chooses i->j)
        if include_edge_usage:
            edge_counter = defaultdict(int)
            for s in range(S):
                path = routes[s]
                for t in range(T - 1):
                    i, j = int(path[t]), int(path[t + 1])
                    edge_counter[(i, j)] += 1
            # normalize to probability
            total_transitions = S * (T - 1)
            edge_usage = {f"{i}->{j}": cnt / total_transitions for (i, j), cnt in edge_counter.items()}
            # top-10 most frequent moves (helps detect bias)
            top_edges = sorted(edge_usage.items(), key=lambda x: -x[1])[:10]
            perf["edge_usage"] = edge_usage
            perf["top_edges"] = top_edges
            if self.summary_text and top_edges:
                text_lines.append(f"- Top moves (probability): {top_edges}")

        # Per-step stats (early vs. late step quality)
        if include_step_stats:
            step_mean = step_costs.mean(axis=0)  # (T,)
            step_std = step_costs.std(axis=0)  # (T,)
            perf["per_step_cost_stats"] = {
                "mean": step_mean.tolist(),
                "std": step_std.tolist()
            }
            text_lines.append(f"- First-step mean cost: {step_mean[0]:.3f}; "
                              f"last-step mean cost: {step_mean[-1]:.3f}")

        # Representative scenarios (best / median / worst) for quick inspection
        order = np.argsort(totals)
        rep_ids = [int(order[0]), int(order[len(order) // 2]), int(order[-1])]
        perf["representative_scenarios"] = {
            "indices": rep_ids,
            "routes": [routes[i].tolist() for i in rep_ids],
            "step_costs": [step_costs[i].tolist() for i in rep_ids],
            "totals": [float(totals[i]) for i in rep_ids]
        }
        b, m, w = rep_ids
        text_lines.append(f"- Representative scenarios -> best:{b}, median:{m}, worst:{w}")
        "\n".join(text_lines)
        return "\n".join(text_lines)
