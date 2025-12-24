import numpy as np


class InventoryAnalyzer:
    def __init__(self, prob, n_train, data_summary='no', algo_performance='no', param_info=None, prompt_version='v2'):
        self.prob = prob
        self.n_train = n_train
        self.data_summary = data_summary
        self.algo_performance = algo_performance
        self.param_info = param_info
        self.version = prompt_version  # 'v1' = old version, 'v2' = new version

    def get_problem_spec(self):
        """
        [
            {
                "instance_id": "test_poisson_L2_c1_2_0",
                "initial_inventory": 0,
                "demand": [
                    94,
                    84,
                    79,
                    93,
                    90,
                    ...
                ],
                "num_periods": 50,
                "holding_cost": 1,
                "lost_sales_cost": 2,
                "lead_time": 2,
                "distribution": "poisson",
                "std_normal": null,
                "pareto_alpha": 3.0
            },
            ...
        ]
        """
        return

    def get_demand_data(self):
        instances = self.prob.load_instances(mode='train', n_traj=self.n_train)
        demand_text = ''
        for idx, traj in enumerate(instances, start=1):
            demand_text += f"Historical demand trajectory $D^{{{idx}}}$: {traj['demand']}\n"
        return

    def get_sim_results(self, indivs, data):
        return

    def _get_sensitivity(
            self,
            indivs,
            max_params: int = 1,
            n_points: int = 5,
            rel_span: float = 0.10,
            timeout: float = 15.0,
            prefer_param_name_keywords=(
                    "base", "stock", "target", "level", "mean", "mu", "safety", "cap", "alpha", "beta"),
    ):
        """
        Wrapper that appends PARAM SENSITIVITY after the performance/diagnostics text returned by _get_temp(indivs).

        It:
        - extracts OPT_PARAM configs from policy code,
        - performs a small local sweep around the parameter initial value,
        - re-evaluates modified code,
        - formats results into prompt-ready sensitivity block(s),
        - returns: _get_temp(indivs) + "\n\n" + sensitivity_text

        Parameters
        ----------
        max_params : sweep at most this many parameters per policy (default 1 to control evaluation budget)
        n_points   : number of sweep points per parameter (default 5)
        rel_span   : sweep range around initial: initial*(1±rel_span) (default ±10%)
        timeout    : per-evaluation timeout (best-effort, only used if we can run in a separate thread)
        """
        import re
        import json
        import ast
        import traceback
        import concurrent.futures

        # ------------------------------------------------------------
        # 0) Helper: locate evaluator
        # ------------------------------------------------------------
        def _locate_evaluator():
            # Priority 1: self.interface_eval.evaluate
            if hasattr(self, "interface_eval") and hasattr(self.interface_eval, "evaluate"):
                return self.interface_eval.evaluate
            # Priority 2: self.prob.interface_eval.evaluate
            if hasattr(self, "prob") and hasattr(self.prob, "interface_eval") and hasattr(self.prob.interface_eval,
                                                                                          "evaluate"):
                return self.prob.interface_eval.evaluate
            # Priority 3: self.prob.evaluate
            if hasattr(self, "prob") and hasattr(self.prob, "evaluate") and callable(self.prob.evaluate):
                return self.prob.evaluate
            # Priority 4: self.evaluate (if you attached it externally)
            if hasattr(self, "evaluate") and callable(self.evaluate):
                return self.evaluate
            return None

        evaluate_fn = _locate_evaluator()

        # ------------------------------------------------------------
        # 1) Helper: parse OPT_PARAM lines in code
        # ------------------------------------------------------------
        def _parse_opt_params(code: str):
            """
            Returns:
              opt_params: dict[param_name] = {"initial":..., "min":..., "max":..., "type":...}
            """
            opt_params = {}
            if not code or not isinstance(code, str):
                return opt_params

            for line in code.splitlines():
                if "OPT_PARAM:" not in line:
                    continue

                # Extract param name from assignment
                m_name = re.match(r"^\s*([A-Za-z_]\w*)\s*=", line)
                if not m_name:
                    continue
                param_name = m_name.group(1)

                # Extract the OPT_PARAM dict substring
                try:
                    idx = line.index("OPT_PARAM:")
                    param_str = line[idx + len("OPT_PARAM:"):].strip()
                except Exception:
                    continue

                # Try JSON first; fallback to python literal
                cfg = None
                try:
                    cfg = json.loads(param_str)
                except Exception:
                    try:
                        cfg = ast.literal_eval(param_str)
                    except Exception:
                        # try a common fix: single quotes -> double quotes
                        try:
                            cfg = json.loads(param_str.replace("'", '"'))
                        except Exception:
                            cfg = None

                if isinstance(cfg, dict):
                    # normalize keys
                    out = {
                        "initial": cfg.get("initial", None),
                        "min": cfg.get("min", None),
                        "max": cfg.get("max", None),
                        "type": cfg.get("type", "float"),
                    }
                    opt_params[param_name] = out

            return opt_params

        # ------------------------------------------------------------
        # 2) Helper: replace parameter assignment line in code (preserve OPT_PARAM comment)
        # ------------------------------------------------------------
        def _replace_one_param(code: str, param_name: str, new_value):
            lines = code.split("\n")
            replaced = False

            for i, line in enumerate(lines):
                if "OPT_PARAM:" not in line:
                    continue
                if not re.match(rf"^\s*{re.escape(param_name)}\s*=", line):
                    continue

                indent = line[:len(line) - len(line.lstrip())]

                # Preserve OPT_PARAM dict if possible
                cfg = None
                try:
                    idx = line.index("OPT_PARAM:")
                    param_str = line[idx + len("OPT_PARAM:"):].strip()
                    try:
                        cfg = json.loads(param_str)
                    except Exception:
                        try:
                            cfg = ast.literal_eval(param_str)
                        except Exception:
                            try:
                                cfg = json.loads(param_str.replace("'", '"'))
                            except Exception:
                                cfg = None
                except Exception:
                    cfg = None

                if isinstance(cfg, dict):
                    cfg["initial"] = float(new_value) if cfg.get("type", "float") != "int" else int(new_value)
                    new_line = f"{indent}{param_name} = {cfg['initial']}  # OPT_PARAM: {json.dumps(cfg)}"
                else:
                    new_line = f"{indent}{param_name} = {new_value}  # Optimized"

                lines[i] = new_line
                replaced = True
                break

            # Fallback: if not found in OPT_PARAM line, do a coarse regex replace on any assignment
            if not replaced:
                for i, line in enumerate(lines):
                    m = re.match(rf"^(\s*){re.escape(param_name)}\s*=\s*([^#\n]+)", line)
                    if m:
                        indent = m.group(1)
                        lines[i] = f"{indent}{param_name} = {new_value}"
                        break

            return "\n".join(lines)

        # ------------------------------------------------------------
        # 3) Helper: summarize avg/holding/lost from evaluation output
        # ------------------------------------------------------------
        # We reuse the same slicing logic idea as in _get_temp: try to infer L,T and slice selling phase.
        def _infer_LT_from_problem():
            # lead time
            L = None
            if hasattr(self, "param") and isinstance(self.param, dict):
                L = self.param.get("lead_time", None) or self.param.get("L", None)
            if L is None and hasattr(self, "prob"):
                if hasattr(self.prob, "lead_time"):
                    L = getattr(self.prob, "lead_time")
            if L is None:
                # try from train instances
                try:
                    inst = self.prob.load_instances(mode="train", n_traj=1)
                    if inst and isinstance(inst[0], dict) and "lead_time" in inst[0]:
                        L = inst[0]["lead_time"]
                except Exception:
                    L = None
            L = int(L) if L is not None else 0

            # selling horizon
            T = None
            try:
                inst = self.prob.load_instances(mode="train", n_traj=1)
                if inst and isinstance(inst[0], dict) and "demand" in inst[0]:
                    T = len(inst[0]["demand"]) - L
            except Exception:
                T = None

            return L, T

        L_global, T_global = _infer_LT_from_problem()

        def _summarize_costs_from_cost_matrix(cost_matrix):
            """
            Returns (avg_total_per_period, avg_holding_per_period, avg_lost_per_period)
            """
            cm = np.asarray(cost_matrix, dtype=float)
            if cm.size == 0:
                return float("nan"), float("nan"), float("nan")

            # cm can be [N, P, 2] or [P, 2]
            if cm.ndim == 2 and cm.shape[1] == 2:
                holding = cm[:, 0]
                lost = cm[:, 1]
                total = holding + lost
                return float(np.mean(total)), float(np.mean(holding)), float(np.mean(lost))

            if cm.ndim != 3 or cm.shape[2] != 2:
                # unknown shape
                return float("nan"), float("nan"), float("nan")

            N = cm.shape[0]
            P = cm.shape[1]

            # Slice selling phase if possible
            if (T_global is not None) and (P == T_global):
                cm_sell = cm
            elif (T_global is not None) and (P == (L_global + T_global)):
                cm_sell = cm[:, L_global:, :]
            elif (T_global is not None) and (P > T_global):
                cm_sell = cm[:, -T_global:, :]
            else:
                cm_sell = cm

            holding = cm_sell[:, :, 0]
            lost = cm_sell[:, :, 1]
            total = holding + lost
            return float(np.mean(total)), float(np.mean(holding)), float(np.mean(lost))

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
            if self.version == 'v2':
                demand_text = '\nDemand trajectories:\n'
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
    - Per-trajectory long-run total cost:
      $\\sum_{{t=L+1}}^{{L+T}} \\Big[ h \\cdot \\max(0,\\, I_t^{{\\pi,n}} + q_{{t,1}}^{{\\,\\pi,n}} - D_t^n) + p \\cdot \\max(0,\\, D_t^n - I_t^{{\\pi,n}} - q_{{t,1}}^{{\\,\\pi,n}}) \\Big]$
      mean = {traj_mean:.2f}, std={traj_std:.2f}, range=({traj_min:.2f}, {traj_max:.2f})
            """)

        performance_summary_processed = "\n".join(summaries)
        return performance_summary_processed
