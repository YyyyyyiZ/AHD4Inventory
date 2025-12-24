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
                    f"\nSection 2 Problem Parameters:\n\n"
                    f"        Below are some problem parameters:\n"
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
            if self.version == 'v2' and self.algo_performance == "temp":
                demand_text = ''
            elif self.version == 'v2':
                demand_text = '\nDemand trajectories:\n'
            for idx, traj in enumerate(instances, start=1):
                if self.version == 'v1':
                    demand_text += f"Trajectory {idx} demand sequence: {traj['demand']}\n"
                    demand_text += f"Trajectory {idx} demand sequence: {traj['demand'][traj['lead_time']:]}\n"
                else:  # v2
                    demand_text += f"Historical demand trajectory $D^{{{idx}}}$: {traj['demand']}\n"
                    # demand_text += f"Historical demand trajectory $D^{{{idx}}}$: {traj['demand'][traj['lead_time']:]}\n"
            return demand_text
        else:  # self.data_summary == 'no'
            return None

    def get_algo_performance(self, indivs):
        if self.algo_performance == 'plain':
            return self._get_plain(indivs, n_sample=3)
        elif self.algo_performance == 'processed':
            return self._get_processed(indivs)
        elif self.algo_performance == 'temp':
            return self._get_temp(indivs)
        elif self.algo_performance == 'temp2':
            return self._get_sensitivity(indivs)
        else:
            return None

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

        def _summarize_from_eval_result(res):
            # res is usually dict: {'avg':..., 'cost_matrix':..., ...}
            if isinstance(res, dict):
                if "cost_matrix" in res and res["cost_matrix"] is not None:
                    return _summarize_costs_from_cost_matrix(res["cost_matrix"])
                # fallback if only avg exists
                if "avg" in res:
                    return float(res["avg"]), float("nan"), float("nan")
            # unknown
            return float("nan"), float("nan"), float("nan")

        # ------------------------------------------------------------
        # 4) Helper: choose which params to sweep (key param selection)
        # ------------------------------------------------------------
        def _select_params(opt_params: dict):
            if not opt_params:
                return []
            names = list(opt_params.keys())

            # Heuristic ranking: prefer names containing keywords, then by range width
            def score(name):
                lname = name.lower()
                kw_bonus = 0
                for kw in prefer_param_name_keywords:
                    if kw in lname:
                        kw_bonus += 10
                cfg = opt_params[name]
                lo, hi = cfg.get("min", None), cfg.get("max", None)
                rng = 0.0
                try:
                    if lo is not None and hi is not None:
                        rng = float(hi) - float(lo)
                except Exception:
                    rng = 0.0
                return (kw_bonus, rng)

            names_sorted = sorted(names, key=lambda n: score(n), reverse=True)
            return names_sorted[:max_params]

        # ------------------------------------------------------------
        # 5) Helper: generate sweep points around initial
        # ------------------------------------------------------------
        def _generate_sweep_values(cfg: dict):
            init = cfg.get("initial", None)
            lo = cfg.get("min", None)
            hi = cfg.get("max", None)
            typ = cfg.get("type", "float")

            # robust defaulting
            try:
                init_f = float(init) if init is not None else None
            except Exception:
                init_f = None
            try:
                lo_f = float(lo) if lo is not None else None
            except Exception:
                lo_f = None
            try:
                hi_f = float(hi) if hi is not None else None
            except Exception:
                hi_f = None

            if init_f is None:
                if lo_f is not None and hi_f is not None:
                    init_f = 0.5 * (lo_f + hi_f)
                else:
                    init_f = 0.0

            # Build local multiplicative sweep
            if init_f != 0:
                mults = np.linspace(1.0 - rel_span, 1.0 + rel_span, n_points)
                vals = [init_f * m for m in mults]
            else:
                # If init == 0, use additive sweep if we have bounds, else tiny symmetric points
                if lo_f is not None and hi_f is not None and hi_f > lo_f:
                    vals = list(np.linspace(lo_f, hi_f, n_points))
                else:
                    vals = [-(n_points // 2) + k for k in range(n_points)]

            # Clip to bounds
            clipped = []
            for v in vals:
                vv = float(v)
                if lo_f is not None:
                    vv = max(lo_f, vv)
                if hi_f is not None:
                    vv = min(hi_f, vv)
                clipped.append(vv)

            # Ensure initial included (clipped)
            init_clip = init_f
            if lo_f is not None:
                init_clip = max(lo_f, init_clip)
            if hi_f is not None:
                init_clip = min(hi_f, init_clip)

            clipped.append(init_clip)

            # Deduplicate while preserving order (and keep sorted by value for readability)
            uniq = sorted(set([float(x) for x in clipped]))
            if typ == "int":
                uniq = sorted(set([int(round(x)) for x in uniq]))

            # If too few points due to clipping, add a couple of evenly spaced points
            if len(uniq) < max(3, n_points) and lo_f is not None and hi_f is not None and hi_f > lo_f:
                extra = np.linspace(lo_f, hi_f, max(3, n_points))
                if typ == "int":
                    extra = [int(round(x)) for x in extra]
                else:
                    extra = [float(x) for x in extra]
                uniq = sorted(set(list(uniq) + list(extra)))

            # Finally, keep it small
            if len(uniq) > n_points:
                # pick points closest to init (for local sensitivity)
                def dist(v):
                    return abs(float(v) - float(init_clip))

                uniq = sorted(uniq, key=dist)[:n_points]
                uniq = sorted(uniq)

            return uniq

        # ------------------------------------------------------------
        # 6) Evaluate sweep points (with best-effort timeout)
        # ------------------------------------------------------------
        def _eval_with_timeout(code: str):
            if evaluate_fn is None:
                raise RuntimeError(
                    "No evaluator found (set self.interface_eval or self.prob.interface_eval or self.prob.evaluate).")

            # Best-effort: run in a thread for timeout support
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(evaluate_fn, code)
                return fut.result(timeout=timeout)

        # ------------------------------------------------------------
        # 7) Build sensitivity text blocks per policy
        # ------------------------------------------------------------
        sens_blocks = []

        for i, indiv in enumerate(indivs, start=1):
            # ---- find code ----
            code = (
                    indiv.get("code", None)
                    or indiv.get("policy_code", None)
                    or indiv.get("optimized_code", None)
                    or indiv.get("impl", None)
            )

            if not isinstance(code, str) or not code.strip():
                sens_blocks.append(
                    f"No.{i} PARAM SENSITIVITY:\n"
                    f"- sensitivity unavailable: missing policy code in indiv['code'/'policy_code'/...]\n"
                )
                continue

            opt_params = _parse_opt_params(code)
            if not opt_params:
                sens_blocks.append(
                    f"No.{i} PARAM SENSITIVITY:\n"
                    f"- no OPT_PARAM found in code (nothing to sweep)\n"
                )
                continue

            chosen = _select_params(opt_params)

            # Baseline metrics from existing indiv cost_matrix (avoid re-evaluating initial point if possible)
            base_avg, base_hold, base_lost = float("nan"), float("nan"), float("nan")
            if "cost_matrix" in indiv and indiv["cost_matrix"] is not None:
                base_avg, base_hold, base_lost = _summarize_costs_from_cost_matrix(indiv["cost_matrix"])

            # Evaluate sweep(s)
            lines = []
            lines.append(f"No.{i} PARAM SENSITIVITY:")

            if evaluate_fn is None:
                lines.append(
                    "- sensitivity unavailable: evaluator not found in InventoryAnalyzer (cannot re-evaluate code).")
                # still show parsed params for debugging
                lines.append(f"- detected OPT_PARAMs = {list(opt_params.keys())}")
                sens_blocks.append("\n".join(lines) + "\n")
                continue

            for pname in chosen:
                cfg = opt_params[pname]
                sweep_vals = _generate_sweep_values(cfg)

                # Identify current/initial value
                p_type = cfg.get("type", "float")
                try:
                    p_init = cfg.get("initial", None)
                    p_init = int(p_init) if p_type == "int" else float(p_init)
                except Exception:
                    p_init = sweep_vals[len(sweep_vals) // 2] if sweep_vals else None

                # Header
                lines.append(f"- {pname} sweep:")
                lines.append("  value -> avg_cost, holding_cost, lost_sales_cost")

                # Cache per value to avoid duplicates
                cache = {}

                for v in sweep_vals:
                    key = (pname, v)
                    if key in cache:
                        avg, hold, lost = cache[key]
                    else:
                        # If v is the incumbent value and we have baseline metrics, reuse baseline
                        is_baseline = False
                        try:
                            if p_init is not None:
                                if p_type == "int":
                                    is_baseline = (int(v) == int(p_init))
                                else:
                                    is_baseline = (abs(float(v) - float(p_init)) < 1e-9)
                        except Exception:
                            is_baseline = False

                        if is_baseline and np.isfinite(base_avg):
                            avg, hold, lost = base_avg, base_hold, base_lost
                        else:
                            try:
                                new_code = _replace_one_param(code, pname, int(v) if p_type == "int" else float(v))
                                res = _eval_with_timeout(new_code)
                                avg, hold, lost = _summarize_from_eval_result(res)
                            except Exception as e:
                                avg, hold, lost = float("nan"), float("nan"), float("nan")
                                # keep a short error in-line (prompt-friendly)
                                err_short = f"{type(e).__name__}: {str(e)[:120]}"
                                lines.append(f"  {v} -> ERROR ({err_short})")
                                continue

                        cache[key] = (avg, hold, lost)

                    # Normal line
                    if np.isfinite(avg):
                        # Keep concise; 2 decimals to match your existing style
                        lines.append(f"  {v} -> avg={avg:.2f}, holding={hold:.2f}, lost={lost:.2f}")
                    else:
                        lines.append(f"  {v} -> avg=nan, holding=nan, lost=nan")

            sens_blocks.append("\n".join(lines) + "\n")

        # ------------------------------------------------------------
        # 8) Combine with performance/diagnostics text from _get_temp
        # ------------------------------------------------------------
        perf_text = self._get_temp(indivs)
        sens_text = "\n".join(sens_blocks).strip()

        if sens_text:
            return perf_text.rstrip() + "\n\n" + sens_text + "\n"
        return perf_text

    def _get_temp(self, indivs):
        """
        Generate a compact-yet-informative performance + diagnostics text block for prompt injection.

        Expected indiv fields (minimum):
          - indiv["order_matrix"]: shape [N, P_order]
          - indiv["cost_matrix"] : shape [N, P_cost, 2] where [:,:,0]=holding_cost, [:,:,1]=lost_sales_cost

        Optional (if your evaluator already logs them; will be used preferentially for counterexamples):
          - indiv["on_hand_matrix"]   : shape [N, T] start-of-period pre-arrival inventory I_t (selling phase)
          - indiv["pipeline_matrix"]  : shape [N, T, L] pipeline vector Q_t at start-of-period (oldest->newest)
          - indiv["demand_matrix"]    : shape [N, T] demand in selling phase

        This function is robust to:
          - cost_matrix being either selling-only (T) or full-horizon (L+T with first L zeros)
          - order_matrix being either full-horizon (L+T) or selling-only (T) (selling-only will be padded with zeros for planning as a best-effort)
        """
        summaries = []

        # ---------------------------
        # Load demand trajectories (authoritative ground truth for counterexamples + fill rate)
        # ---------------------------
        instances = self.prob.load_instances(mode="train", n_traj=self.n_train)

        demands_full = []
        for traj in instances:
            d = None
            if isinstance(traj, dict):
                d = traj.get("demand", None)
                if d is None:
                    d = traj.get("demands", None)
            if d is not None:
                demands_full.append(np.asarray(d, dtype=float))

        # ---------------------------
        # Infer core parameters (L, T, h, p) robustly
        # ---------------------------
        def _safe_get(dct, keys, default=None):
            if not isinstance(dct, dict):
                return default
            for k in keys:
                if k in dct and dct[k] is not None:
                    return dct[k]
            return default

        # Lead time L
        L = None
        L = _safe_get(getattr(self, "param", None), ["lead_time", "L", "leadtime"], None)
        if L is None and len(instances) > 0 and isinstance(instances[0], dict):
            L = instances[0].get("lead_time", None)
        if L is None:
            # best-effort: if demand has leading zeros, still not safe to infer; fallback to 0
            L = 0
        L = int(L)

        # Horizon_total and selling horizon T
        horizon_total = len(demands_full[0]) if len(demands_full) > 0 else None
        T = None
        if horizon_total is not None and horizon_total >= L:
            T = horizon_total - L

        # Costs h, p
        h = _safe_get(getattr(self, "param", None), ["holding_cost", "h"], None)
        p = _safe_get(getattr(self, "param", None), ["lost_sales_cost", "lostsale_cost", "p"], None)
        if h is None:
            h = getattr(self.prob, "holding_cost", None)
        if p is None:
            p = getattr(self.prob, "lost_sales_cost", None)
        if h is None:
            h = 1.0
        if p is None:
            p = 2.0
        h = float(h)
        p = float(p)

        # Selling-phase demand arrays (for fill rate)
        demands_selling = []
        if horizon_total is not None and len(demands_full) > 0 and horizon_total > L:
            for d in demands_full:
                demands_selling.append(d[L:])
        else:
            demands_selling = demands_full

        # ---------------------------
        # Formatting helpers
        # ---------------------------
        def _fmt_scalar(x):
            try:
                xf = float(x)
            except Exception:
                return str(x)
            if not np.isfinite(xf):
                return "nan"
            r = round(xf)
            if abs(xf - r) < 1e-6:
                return str(int(r))
            return f"{xf:.2f}"

        def _fmt_list(xs):
            return "[" + ", ".join(_fmt_scalar(v) for v in xs) + "]"

        def _fmt_pairs(pairs, val_fmt="{:.2f}"):
            # pairs = [(idx, val), ...]
            out = []
            for k, v in pairs:
                try:
                    out.append(f"({int(k)}, {val_fmt.format(float(v))})")
                except Exception:
                    out.append(f"({k}, {v})")
            return "[" + ", ".join(out) + "]"

        # ---------------------------
        # Main loop: build performance+diagnostics for each indiv
        # ---------------------------
        for i, indiv in enumerate(indivs, start=1):
            order_matrix = np.asarray(indiv.get("order_matrix", []), dtype=float)
            cost_matrix = np.asarray(indiv.get("cost_matrix", []), dtype=float)

            if cost_matrix.size == 0:
                summaries.append(
                    f"No.{i} incumbent policy:\n"
                    f"INCUMBENT METRICS:\n"
                    f"- (missing cost_matrix)\n"
                )
                continue

            N = int(cost_matrix.shape[0])
            P_cost = int(cost_matrix.shape[1])

            # Infer T if still unknown
            T_local = T if T is not None else P_cost
            L_local = L

            # Slice selling-phase costs robustly
            if P_cost == T_local:
                cost_selling = cost_matrix
            elif P_cost == (L_local + T_local):
                cost_selling = cost_matrix[:, L_local:, :]
            elif P_cost > T_local:
                # take last T_local periods as selling (best-effort)
                cost_selling = cost_matrix[:, -T_local:, :]
            else:
                # shorter-than-expected; use as-is
                cost_selling = cost_matrix

            holding_costs = cost_selling[:, :, 0]
            lost_costs = cost_selling[:, :, 1]
            total_costs = holding_costs + lost_costs

            mean_total = float(np.mean(total_costs))
            std_total = float(np.std(total_costs))
            mean_holding = float(np.mean(holding_costs))
            mean_lost = float(np.mean(lost_costs))

            # Units
            lost_units = (lost_costs / p) if p != 0 else np.zeros_like(lost_costs)
            ending_inventory = (holding_costs / h) if h != 0 else np.zeros_like(holding_costs)

            # Fill rate (use demand history if available)
            total_lost_units = float(np.sum(lost_units))
            total_demand_units = float("nan")
            if len(demands_selling) >= N:
                # align to cost_selling horizon length
                T_used = int(holding_costs.shape[1])
                total_demand_units = float(np.sum([np.sum(demands_selling[n][:T_used]) for n in range(N)]))
            fill_rate = (
                1.0 - total_lost_units / total_demand_units
                if (np.isfinite(total_demand_units) and total_demand_units > 0)
                else float("nan")
            )
            stockout_rate = float(np.mean(lost_units > 1e-12))

            # Orders: selling-slice + best-effort full replay array
            avg_order = float("nan")
            order_var = float("nan")
            order_std = float("nan")
            max_order = float("nan")
            orders_replay = None  # shape [N, horizon_total] best-effort
            orders_selling = None

            if order_matrix.size > 0:
                P_order = int(order_matrix.shape[1])

                # Define a selling slice consistent with cost_selling length
                T_used = int(holding_costs.shape[1])
                if T is not None and P_order == (L_local + T_local):
                    orders_selling = order_matrix[:, L_local:L_local + T_used]
                elif T is not None and P_order == T_local:
                    orders_selling = order_matrix[:, :T_used]
                else:
                    # fallback: last T_used
                    orders_selling = order_matrix[:, -T_used:] if P_order >= T_used else order_matrix

                avg_order = float(np.mean(orders_selling))
                order_var = float(np.var(orders_selling))
                order_std = float(np.std(orders_selling))
                max_order = float(np.max(orders_selling))

                # Prepare orders for replay to recover pipeline states (needs horizon_total)
                if horizon_total is not None:
                    if P_order == horizon_total:
                        orders_replay = order_matrix[:N, :horizon_total]
                    elif T is not None and P_order == (L_local + T_local):
                        # already full horizon
                        orders_replay = order_matrix[:N, : (L_local + T_local)]
                    elif T is not None and P_order == T_local:
                        # best-effort: pad planning with zeros
                        if L_local > 0:
                            orders_replay = np.concatenate(
                                [np.zeros((min(N, order_matrix.shape[0]), L_local)), order_matrix[:N, :T_local]],
                                axis=1
                            )
                        else:
                            orders_replay = order_matrix[:N, :T_local]
                    else:
                        # crop/pad to horizon_total
                        if P_order >= horizon_total:
                            orders_replay = order_matrix[:N, :horizon_total]
                        else:
                            pad = horizon_total - P_order
                            orders_replay = np.concatenate(
                                [order_matrix[:N, :], np.zeros((min(N, order_matrix.shape[0]), pad))],
                                axis=1
                            )

            # ---------------------------
            # DIAGNOSTICS 1) period-wise profile (selling period index 1..T_used)
            # ---------------------------
            holding_profile = np.mean(holding_costs, axis=0)  # length T_used
            lost_units_profile = np.mean(lost_units, axis=0)  # length T_used

            top_hold_idx = np.argsort(-holding_profile)[:5]
            top_lost_idx = np.argsort(-lost_units_profile)[:5]

            top_hold_pairs = [(int(k + 1), float(holding_profile[k])) for k in top_hold_idx]
            top_lost_pairs = [(int(k + 1), float(lost_units_profile[k])) for k in top_lost_idx]

            # ---------------------------
            # DIAGNOSTICS 2) counterexample states
            # ---------------------------
            lost_state_lines = []
            over_state_lines = []

            # Preferred: use evaluator-logged matrices if available
            has_logged_states = all(k in indiv for k in ("on_hand_matrix", "pipeline_matrix", "demand_matrix"))
            if has_logged_states:
                I_mat = np.asarray(indiv["on_hand_matrix"], dtype=float)
                Q_mat = np.asarray(indiv["pipeline_matrix"], dtype=float)
                D_mat = np.asarray(indiv["demand_matrix"], dtype=float)

                rec_lost = []
                rec_over = []
                N_use = min(N, I_mat.shape[0], Q_mat.shape[0], D_mat.shape[0])
                T_use = min(int(holding_costs.shape[1]), I_mat.shape[1], D_mat.shape[1], Q_mat.shape[1])

                for n in range(N_use):
                    for t_idx in range(T_use):
                        I0 = float(I_mat[n, t_idx])
                        Q0 = list(Q_mat[n, t_idx].tolist())
                        D0 = float(D_mat[n, t_idx])
                        lu = float(lost_units[n, t_idx])
                        ei = float(ending_inventory[n, t_idx])
                        if lu > 1e-12:
                            rec_lost.append((lu, I0, Q0, D0))
                        rec_over.append((ei, I0, Q0, D0))

                rec_lost.sort(key=lambda x: x[0], reverse=True)
                rec_over.sort(key=lambda x: x[0], reverse=True)

                for lu, I0, Q0, D0 in rec_lost[:10]:
                    lost_state_lines.append(
                        f"(on_hand={_fmt_scalar(I0)}, pipeline_orders={_fmt_list(Q0)}, demand={_fmt_scalar(D0)}, lost_units={_fmt_scalar(lu)})"
                    )
                for ei, I0, Q0, D0 in rec_over[:10]:
                    over_state_lines.append(
                        f"(on_hand={_fmt_scalar(I0)}, pipeline_orders={_fmt_list(Q0)}, demand={_fmt_scalar(D0)}, ending_inventory={_fmt_scalar(ei)})"
                    )

            # Otherwise: replay dynamics using (demand history + recorded orders)
            else:
                can_replay = (
                        (orders_replay is not None)
                        and (len(demands_full) > 0)
                        and (horizon_total is not None)
                        and (L_local >= 0)
                )
                if can_replay:
                    N_sim = min(N, orders_replay.shape[0], len(demands_full))
                    rec_lost = []
                    rec_over = []

                    for n in range(N_sim):
                        I = 0.0
                        Q = [0.0] * L_local
                        d_full = demands_full[n]
                        o_full = orders_replay[n]

                        for t in range(horizon_total):
                            q_arrive = Q[0] if L_local > 0 else 0.0
                            D = float(d_full[t])
                            a = float(o_full[t]) if t < o_full.shape[0] else 0.0

                            if t >= L_local:
                                lu = max(0.0, D - I - q_arrive)
                                ei = max(0.0, I + q_arrive - D)
                                if lu > 1e-12:
                                    rec_lost.append((lu, I, Q.copy(), D))
                                rec_over.append((ei, I, Q.copy(), D))

                            # transition
                            I = max(0.0, I + q_arrive - D)
                            if L_local > 0:
                                if L_local > 1:
                                    Q = Q[1:] + [a]
                                else:
                                    Q = [a]

                    rec_lost.sort(key=lambda x: x[0], reverse=True)
                    rec_over.sort(key=lambda x: x[0], reverse=True)

                    for lu, I0, Q0, D0 in rec_lost[:10]:
                        lost_state_lines.append(
                            f"(on_hand={_fmt_scalar(I0)}, pipeline_orders={_fmt_list(Q0)}, demand={_fmt_scalar(D0)}, lost_units={_fmt_scalar(lu)})"
                        )
                    for ei, I0, Q0, D0 in rec_over[:10]:
                        over_state_lines.append(
                            f"(on_hand={_fmt_scalar(I0)}, pipeline_orders={_fmt_list(Q0)}, demand={_fmt_scalar(D0)}, ending_inventory={_fmt_scalar(ei)})"
                        )
                else:
                    lost_state_lines = ["(state reconstruction unavailable: missing demand history or order_matrix)"]
                    over_state_lines = ["(state reconstruction unavailable: missing demand history or order_matrix)"]

            # Pretty blocks
            lost_block = "\n".join([f"     {j}) {line}" for j, line in enumerate(lost_state_lines[:10], start=1)])
            over_block = "\n".join([f"     {j}) {line}" for j, line in enumerate(over_state_lines[:10], start=1)])

            # Compose final text for this policy
            summaries.append(
                f"No.{i} incumbent policy:\n"
                f"\n"
                f"INCUMBENT METRICS:\n"
                f"- avg total cost per period = {mean_total:.2f} (std={std_total:.2f})\n"
                f"- holding cost per period = {mean_holding:.2f}\n"
                f"- lost-sales cost per period = {mean_lost:.2f}\n"
                f"- fill rate (1 - lost_units / total_demand) = {_fmt_scalar(fill_rate)} "
                f"(total_demand={_fmt_scalar(total_demand_units)}, total_lost_units={_fmt_scalar(total_lost_units)})\n"
                f"- stockout rate (P(lost_units>0)) = {stockout_rate:.4f}\n"
                f"- avg order per period (selling) = {_fmt_scalar(avg_order)}\n"
                f"- order variance (selling) = {_fmt_scalar(order_var)} (std={_fmt_scalar(order_std)}, max={_fmt_scalar(max_order)})\n"
                f"\n"
                f"DIAGNOSTICS:\n"
                f"1) Period-wise cost profile (selling period index 1..T):\n"
                f"   - Top 5 periods with highest holding cost: {_fmt_pairs(top_hold_pairs)}\n"
                f"   - Top 5 periods with highest lost-sales (avg lost units): {_fmt_pairs(top_lost_pairs)}\n"
                f"2) Counterexample states:\n"
                f"   - Top 10 states causing lost-sales (on_hand, pipeline_orders, demand, lost_units):\n"
                f"{lost_block}\n"
                f"   - Top 10 states causing overstock (on_hand, pipeline_orders, demand, ending_inventory):\n"
                f"{over_block}\n"
            )
        # print(summaries)

        return "\n\n".join(summaries)

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
