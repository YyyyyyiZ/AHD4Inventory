import numpy as np
import json
import os


class InventoryAnalyzer:
    def __init__(self, prob, n_train, data_summary='no', algo_performance='no', param_info=None, prompt_version='v2'):
        self.prob = prob
        self.n_train = n_train
        self.data_summary = data_summary
        self.algo_performance = algo_performance
        self.param_info = param_info
        self.version = prompt_version  # 'v1' = old version, 'v2' = new version

    def get_problem_spec(self):
        """Read ProblemSpec.json from the current directory and fill (L,T,h,p)."""
        # 1) infer params from first train instance (same as before)
        instances = self.prob.load_instances(mode="train", n_traj=1)
        inst0 = instances[0] if isinstance(instances, (list, tuple)) else instances

        L = int(inst0.get("lead_time", 0) or 0)
        h = float(inst0.get("holding_cost", 0.0) or 0.0)
        p = float(inst0.get("lost_sales_cost", 0.0) or 0.0)
        init_inv = float(inst0.get("initial_inventory", 0.0) or 0.0)
        demand0 = inst0.get("demand", []) or []

        T = inst0.get("num_periods", None)
        if T is None:
            T = max(0, len(demand0) - L) if isinstance(demand0, (list, tuple)) and len(demand0) >= L else 0
        else:
            try:
                T = int(T)
            except Exception:
                T = 0

        if isinstance(demand0, (list, tuple)) and len(demand0) > 0:
            implied_T = (len(demand0) - L) if (len(demand0) >= L) else len(demand0)
            if implied_T > 0 and implied_T != T:
                T = implied_T

        # 2) read + fill template
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir)
        with open(f"{file_path}/ProblemSpec.json", "r", encoding="utf-8") as f:
            spec = json.loads(f.read())

        spec["L"] = int(L)
        spec["T"] = int(T)
        spec["h"] = float(h)
        spec["p"] = float(p)

        # optional: align initial inventory if the template has this field
        if isinstance(spec.get("initial_state", None), dict):
            spec["initial_state"]["I_1"] = float(init_inv)

        return json.dumps(spec, indent=2, ensure_ascii=False)

    def get_demand_data(self):
        instances = self.prob.load_instances(mode='train', n_traj=self.n_train)
        demand_text = ''
        for idx, traj in enumerate(instances, start=1):
            demand_text += f"Historical demand trajectory $D^{{{idx}}}$: {traj['demand']}\n"
        return demand_text

    def get_demand_stats(self):
        instances = self.prob.load_instances(mode='train', n_traj=self.n_train)

        # Collect pooled demand observations (excluding lead time periods)
        all_demand = []
        for traj in instances:
            d = traj.get('demand', [])
            lead_time = traj.get('lead_time', 0)
            # Only include actual demand from selling periods, skip lead time zeros
            actual_demand = d[lead_time:]
            for v in actual_demand:
                try:
                    all_demand.append(float(v))
                except Exception:
                    pass

        n_obs = len(all_demand)
        d_sorted = sorted(all_demand)

        # pooled mean / std (population std, ddof=0)
        mean = sum(all_demand) / float(n_obs)
        var = 0.0
        for x in all_demand:
            dx = x - mean
            var += dx * dx
        var /= float(n_obs)
        std = var ** 0.5

        d_min = d_sorted[0]
        d_max = d_sorted[-1]

        # empirical quantile with linear interpolation (Type-7 style)
        def _quantile(q):
            n = len(d_sorted)
            if n == 1:
                return float(d_sorted[0])
            if q <= 0.0:
                return float(d_sorted[0])
            if q >= 1.0:
                return float(d_sorted[-1])
            pos = q * float(n - 1)
            lo = int(pos)  # floor (pos >= 0)
            hi = lo + 1
            if hi >= n:
                hi = n - 1
            w = pos - float(lo)
            return float(d_sorted[lo] + w * (d_sorted[hi] - d_sorted[lo]))

        # build quantile table (0%,5%,...,100%)
        q_lines = []
        q_lines.append("Percentile | Demand")
        q_lines.append("---|---")
        k = 0
        while k <= 20:
            q = 0.05 * float(k)
            val = _quantile(q)
            pct = int(round(100.0 * q))
            q_lines.append(f"{pct}% | {val:.3f}")
            k += 1

        stats_text = ""
        stats_text += "Demand Statistics\n"
        stats_text += f"- demand mean: {mean:.6f}\n"
        stats_text += f"- demand std: {std:.6f}\n"
        stats_text += "\nQuantiles (5% increments):\n"
        stats_text += "\n".join(q_lines) + "\n\n"

        print(stats_text)

        return stats_text

    def get_sim_results(self, indivs, data):
        """Evaluate candidate policies and return a prompt-ready simulation summary (JSON-like text).

        Parameters
        ----------
        indivs : list of dict
            Each dict should contain a 'code' field (Python policy code).
        data : str
            DemandAgent output. Expected to contain selected trajectory ids (typically 1-based).
        """
        # ---------- helpers (no extra imports) ----------
        def _safe_float(x, default=0.0):
            try:
                return float(x)
            except Exception:
                return float(default)

        def _safe_int(x, default=0):
            try:
                return int(x)
            except Exception:
                return int(default)

        def _extract_ids(text, n_max):
            """Best-effort extraction of trajectory ids from a small JSON-ish text."""
            if not isinstance(text, str):
                return []
            s = text
            lower = s.lower()
            # common keys, in priority order
            keys = [
                'selected_trajectory_ids',
                'trajectory_ids',
                'selected_ids',
                'traj_ids',
                'trajectory_id',
                'ids',
            ]
            bracket = None
            for k in keys:
                pos = lower.find(k)
                if pos != -1:
                    lb = s.find('[', pos)
                    rb = s.find(']', lb+1) if lb != -1 else -1
                    if lb != -1 and rb != -1 and rb > lb:
                        bracket = s[lb+1:rb]
                        break
            if bracket is None:
                # fallback: first bracketed list in the text
                lb = s.find('[')
                rb = s.find(']', lb+1) if lb != -1 else -1
                if lb != -1 and rb != -1 and rb > lb:
                    bracket = s[lb+1:rb]
            if bracket is None:
                return []
            parts = bracket.replace('\n', ' ').split(',')
            ids = []
            for part in parts:
                token = ''.join(ch for ch in part if (ch.isdigit() or ch == '-'))
                if token in ('', '-'):
                    continue
                try:
                    ids.append(int(token))
                except Exception:
                    continue
            # clamp and deduplicate, preserve order
            seen = set()
            cleaned = []
            for v in ids:
                if v in seen:
                    continue
                seen.add(v)
                cleaned.append(v)
            # do not clamp here; caller will map to available N
            return cleaned[:max(0, int(n_max))] if n_max is not None else cleaned

        def _locate_evaluate():
            """Find an evaluate(callable) in self / prob."""
            if hasattr(self, 'interface_eval') and hasattr(self.interface_eval, 'evaluate'):
                return getattr(self.interface_eval, 'evaluate')
            if hasattr(self.prob, 'interface_eval') and hasattr(self.prob.interface_eval, 'evaluate'):
                return getattr(self.prob.interface_eval, 'evaluate')
            if hasattr(self.prob, 'evaluate') and callable(getattr(self.prob, 'evaluate')):
                return getattr(self.prob, 'evaluate')
            if hasattr(self, 'evaluate') and callable(getattr(self, 'evaluate')):
                return getattr(self, 'evaluate')
            return None

        def _slice_selling(arr, L, T):
            """Slice an array over time to the selling window (best-effort)."""
            if arr is None:
                return None, 0
            if len(arr.shape) == 1:
                P = arr.shape[0]
                if P == T:
                    return arr, L
                if P == L + T and L < P:
                    return arr[L:], L
                if P > T:
                    return arr[-T:], L
                return arr, L
            # arr has time axis at -1 or 1; here we only use time axis=1
            if len(arr.shape) >= 2:
                P = arr.shape[1]
                if P == T:
                    return arr, L
                if P == L + T and L < P:
                    return arr[:, L:], L
                if P > T:
                    return arr[:, -T:], L
                return arr, L
            return arr, L

        def _build_full_actions(order_row, L, demand_len):
            """Align order decisions to a full horizon of length demand_len (best-effort)."""
            if order_row is None:
                return [0.0] * int(demand_len)
            order_list = list(order_row.tolist()) if hasattr(order_row, 'tolist') else list(order_row)
            P = len(order_list)
            if P == demand_len:
                return [float(x) for x in order_list]
            if demand_len >= L and P == demand_len - L:
                return [0.0] * int(L) + [float(x) for x in order_list]
            if P < demand_len:
                pad = demand_len - P
                return [0.0] * int(pad) + [float(x) for x in order_list]
            # P > demand_len
            return [float(x) for x in order_list[-demand_len:]]

        # ---------- load instances / parameters ----------
        try:
            instances = self.prob.load_instances(mode='train', n_traj=self.n_train)
        except Exception:
            instances = []

        if not instances:
            return '{"error": "No training instances available."}'

        inst0 = instances[0]
        L = _safe_int(inst0.get('lead_time', 0), 0)
        h = _safe_float(inst0.get('holding_cost', 0.0), 0.0)
        p = _safe_float(inst0.get('lost_sales_cost', 0.0), 0.0)
        demand0 = inst0.get('demand', []) or []
        # selling horizon
        T = inst0.get('num_periods', None)
        if T is None:
            T = max(0, len(demand0) - L) if isinstance(demand0, (list, tuple)) else 0
        T = _safe_int(T, max(0, len(demand0) - L) if isinstance(demand0, (list, tuple)) else 0)
        if isinstance(demand0, (list, tuple)) and len(demand0) > 0:
            implied_T = len(demand0) - L if len(demand0) >= L else len(demand0)
            if implied_T > 0:
                T = implied_T

        N_total = len(instances)
        # DemandAgent-selected trajectory ids
        raw_ids = _extract_ids(data, n_max=N_total)
        if not raw_ids:
            # fallback: use all, but keep it small to control prompt size
            raw_ids = list(range(1, min(N_total, 10) + 1))

        # Determine whether ids are 0-based or 1-based
        min_id = min(raw_ids) if raw_ids else 1
        max_id = max(raw_ids) if raw_ids else 0
        if min_id == 0 and max_id <= (N_total - 1):
            sel_idx = [i for i in raw_ids if 0 <= i < N_total]
            sel_ids_1based = [i + 1 for i in sel_idx]
        else:
            sel_idx = [i - 1 for i in raw_ids if 1 <= i <= N_total]
            sel_ids_1based = [i + 1 for i in sel_idx]

        if not sel_idx:
            sel_idx = list(range(0, min(N_total, 10)))
            sel_ids_1based = [i + 1 for i in sel_idx]

        # ---------- evaluate policies ----------
        evaluate_fn = _locate_evaluate()
        if evaluate_fn is None:
            return '{"error": "No evaluation interface (interface_eval.evaluate) found."}'

        policies_out = []
        for pol_i, indiv in enumerate(indivs, start=1):
            code = ''
            if isinstance(indiv, dict):
                code = indiv.get('code', indiv.get('policy_code', indiv.get('python_code', '')))
            else:
                code = str(indiv)

            # Run evaluation (best-effort). We do not re-implement simulation here.
            eval_error = None
            eval_result = None
            try:
                executor = getattr(self, 'executor', None)
                if executor is None:
                    executor = getattr(self.prob, 'executor', None)
                timeout = getattr(self, 'timeout', None)
                if timeout is None:
                    timeout = getattr(self.prob, 'timeout', None)

                if executor is not None and hasattr(executor, 'submit'):
                    future = executor.submit(evaluate_fn, code)
                    if timeout is not None:
                        eval_result = future.result(timeout=timeout)
                    else:
                        eval_result = future.result()
                else:
                    eval_result = evaluate_fn(code)
            except Exception as e:
                eval_error = str(e)

            # Basic payload
            policy_payload = {
                'policy_index': pol_i,
                'error': eval_error,
            }

            if not isinstance(eval_result, dict):
                # If the evaluator returns a scalar objective, still report it.
                if eval_error is None and eval_result is not None:
                    policy_payload['avg_total_cost_per_period'] = _safe_float(eval_result, 0.0)
                policies_out.append(policy_payload)
                continue

            # Extract matrices
            cm = eval_result.get('cost_matrix', None)
            om = eval_result.get('order_matrix', None)
            try:
                cm = np.array(cm) if cm is not None else None
            except Exception:
                cm = None
            try:
                om = np.array(om) if om is not None else None
            except Exception:
                om = None

            # Filter selected trajectories if shapes match
            cm_sel = cm
            if cm is not None and cm.ndim >= 2 and cm.shape[0] == N_total:
                cm_sel = cm[sel_idx]
            om_sel = om
            if om is not None and om.ndim >= 2 and om.shape[0] == N_total:
                om_sel = om[sel_idx]

            # If cost matrix is missing, we cannot compute detailed diagnostics reliably
            if cm_sel is None or cm_sel.ndim != 3 or cm_sel.shape[2] < 2:
                # Still pass through aggregate objectives if available
                if 'avg' in eval_result:
                    policy_payload['avg_total_cost_per_period'] = _safe_float(eval_result.get('avg'), 0.0)
                if 'lower' in eval_result:
                    policy_payload['lower'] = _safe_float(eval_result.get('lower'), 0.0)
                if 'upper' in eval_result:
                    policy_payload['upper'] = _safe_float(eval_result.get('upper'), 0.0)
                policies_out.append(policy_payload)
                continue

            # Slice to selling window
            cm_sell, period_offset = _slice_selling(cm_sel, L, T)
            holding_costs = cm_sell[:, :, 0]
            lost_costs = cm_sell[:, :, 1]
            total_costs = holding_costs + lost_costs

            mean_total = float(np.mean(total_costs))
            std_total = float(np.std(total_costs))
            mean_hold = float(np.mean(holding_costs))
            mean_lost = float(np.mean(lost_costs))

            # Orders (optional)
            avg_order = None
            var_order = None
            om_sell = None
            if om_sel is not None and om_sel.ndim >= 2:
                om_sell, _ = _slice_selling(om_sel, L, T)
                try:
                    avg_order = float(np.mean(om_sell))
                    var_order = float(np.var(om_sell))
                except Exception:
                    avg_order, var_order = None, None

            # Fill rate (units) from lost costs if p>0
            fill_rate = None
            lost_units = None
            if p > 0:
                lost_units = lost_costs / p
                # Demand totals over selected trajectories for matching horizon length
                total_demand = 0.0
                for local_j, global_idx in enumerate(sel_idx):
                    d = instances[global_idx].get('demand', []) or []
                    if isinstance(d, (list, tuple)):
                        if len(d) >= L + cm_sell.shape[1]:
                            d_sell = d[L:L + cm_sell.shape[1]]
                        elif len(d) >= cm_sell.shape[1]:
                            d_sell = d[:cm_sell.shape[1]]
                        else:
                            d_sell = d
                        total_demand += float(np.sum(np.array(d_sell, dtype=float))) if d_sell else 0.0
                total_lost = float(np.sum(lost_units)) if lost_units is not None else 0.0
                if total_demand > 0:
                    fill_rate = float(max(0.0, min(1.0, 1.0 - total_lost / total_demand)))
                else:
                    fill_rate = None

            # Period-wise diagnostics
            diag = {}
            try:
                avg_hold_per_period = np.mean(holding_costs, axis=0)
                top_hold_idx = np.argsort(-avg_hold_per_period)[:5]
                diag['top_holding_periods'] = [
                    [int(period_offset + int(t) + 1), float(avg_hold_per_period[t])]
                    for t in top_hold_idx
                ]
            except Exception:
                diag['top_holding_periods'] = []

            try:
                if lost_units is None and p > 0:
                    lost_units = lost_costs / p
                if lost_units is not None:
                    avg_lost_units_period = np.mean(lost_units, axis=0)
                    top_lost_idx = np.argsort(-avg_lost_units_period)[:5]
                    diag['top_lost_sales_periods'] = [
                        [int(period_offset + int(t) + 1), float(avg_lost_units_period[t])]
                        for t in top_lost_idx
                    ]
                else:
                    diag['top_lost_sales_periods'] = []
            except Exception:
                diag['top_lost_sales_periods'] = []

            # Counterexample states (best-effort reconstruction from orders + demand)
            lost_states = []
            over_states = []
            try:
                # Need per-trajectory order decisions; if missing, skip
                if om_sel is not None and om_sel.ndim == 2:
                    for local_j, global_idx in enumerate(sel_idx):
                        demand_full = instances[global_idx].get('demand', []) or []
                        if not isinstance(demand_full, (list, tuple)):
                            continue
                        demand_len = len(demand_full)
                        orders_row = om_sel[local_j] if om_sel.shape[0] == len(sel_idx) else om_sel[global_idx]
                        actions_full = _build_full_actions(orders_row, L, demand_len)
                        I = 0.0
                        Q = [0.0] * int(L)
                        for t0 in range(demand_len):
                            D_t = float(demand_full[t0])
                            q_arrive = float(Q[0]) if L > 0 else 0.0
                            available = I + q_arrive
                            lost_u = max(0.0, D_t - available)
                            end_inv = max(0.0, available - D_t)
                            # selling phase periods: t0 >= L (0-based)
                            if t0 >= L:
                                if lost_u > 0:
                                    lost_states.append([float(I), [float(x) for x in Q], float(D_t), float(lost_u)])
                                if end_inv > 0:
                                    over_states.append([float(I), [float(x) for x in Q], float(D_t), float(end_inv)])
                            # update state
                            I = end_inv
                            if L > 0:
                                # place order at period t0 (start), then pipeline shifts to next period
                                a_t = float(actions_full[t0]) if t0 < len(actions_full) else 0.0
                                Q = Q[1:] + [a_t]
            except Exception:
                pass

            # Keep top events by severity
            try:
                lost_states_sorted = sorted(lost_states, key=lambda x: x[3], reverse=True)[:10]
            except Exception:
                lost_states_sorted = lost_states[:10]
            try:
                over_states_sorted = sorted(over_states, key=lambda x: x[3], reverse=True)[:10]
            except Exception:
                over_states_sorted = over_states[:10]
            diag['top_lost_sales_states'] = lost_states_sorted
            diag['top_overstock_states'] = over_states_sorted

            # Attach metrics
            policy_payload.update({
                'avg_total_cost_per_period': mean_total,
                'std_total_cost_per_period': std_total,
                'avg_holding_cost_per_period': mean_hold,
                'avg_lost_sales_cost_per_period': mean_lost,
                'fill_rate': fill_rate,
                'avg_order': avg_order,
                'order_variance': var_order,
                'diagnostics': diag,
            })

            # Pass-through common evaluation outputs (if present)
            for k in ('avg', 'test_obj', 'lower', 'upper'):
                if k in eval_result:
                    policy_payload[k] = eval_result.get(k)

            policies_out.append(policy_payload)

        # ---------- format JSON-like output ----------
        # Manual formatting to avoid json import. Keys/strings use double quotes.
        def _json_escape(s):
            if s is None:
                return ''
            return str(s).replace('\\', '\\\\').replace('"', '\\"')

        out_lines = []
        out_lines.append('{')
        out_lines.append(f'  "selected_trajectory_ids": {sel_ids_1based},')
        out_lines.append('  "policies": [')
        for j, pol in enumerate(policies_out):
            comma = ',' if j < len(policies_out) - 1 else ''
            out_lines.append('    {')
            out_lines.append(f'      "policy_index": {pol.get("policy_index")},')
            if pol.get('error') is not None:
                out_lines.append(f'      "error": "{_json_escape(pol.get("error"))}"')
                out_lines.append('    }' + comma)
                continue
            # numeric fields
            def _maybe_num_line(key, last=False):
                if key in pol and pol[key] is not None:
                    v = pol[key]
                    return f'      "{key}": {v}' + ('' if last else ',')
                return None

            num_keys = [
                'avg_total_cost_per_period',
                'std_total_cost_per_period',
                'avg_holding_cost_per_period',
                'avg_lost_sales_cost_per_period',
                'fill_rate',
                'avg_order',
                'order_variance',
            ]
            for k in num_keys:
                line = _maybe_num_line(k, last=False)
                if line:
                    out_lines.append(line)

            # diagnostics
            diag = pol.get('diagnostics', {}) if isinstance(pol.get('diagnostics', {}), dict) else {}
            out_lines.append('      "diagnostics": {')
            out_lines.append(f'        "top_holding_periods": {diag.get("top_holding_periods", [])},')
            out_lines.append(f'        "top_lost_sales_periods": {diag.get("top_lost_sales_periods", [])},')
            out_lines.append(f'        "top_lost_sales_states": {diag.get("top_lost_sales_states", [])},')
            out_lines.append(f'        "top_overstock_states": {diag.get("top_overstock_states", [])}')
            out_lines.append('      }')
            out_lines.append('    }' + comma)
        out_lines.append('  ]')
        out_lines.append('}')
        return "\n".join(out_lines)

    def _get_eval_matrices(self, indiv):
        order_matrix = None
        cost_matrix = None
        if isinstance(indiv, dict):
            order_matrix = indiv.get("order_matrix")
            cost_matrix = indiv.get("cost_matrix")
        if order_matrix is not None and cost_matrix is not None:
            return order_matrix, cost_matrix, None

        code = ''
        if isinstance(indiv, dict):
            code = indiv.get('code', indiv.get('policy_code', indiv.get('python_code', '')))
        else:
            code = str(indiv)

        try:
            eval_result = self.prob.evaluate(code)
        except Exception as exc:
            return None, None, str(exc)

        order_matrix = eval_result.get('order_matrix')
        cost_matrix = eval_result.get('cost_matrix')
        if order_matrix is None or cost_matrix is None:
            return None, None, "missing order_matrix or cost_matrix from evaluate()"
        return order_matrix, cost_matrix, None

    def get_algo_performance(self, indivs):
        if self.algo_performance == 'plain':
            return self._get_plain(indivs, n_sample=3)
        if self.algo_performance == 'processed':
            return self._get_processed(indivs)
        return None

    def _get_plain(self, indivs, n_sample):
        summaries = []
        for i, indiv in enumerate(indivs, start=1):
            order_matrix, cost_matrix, err = self._get_eval_matrices(indiv)
            if err is not None:
                summaries.append(f"\nNo.{i} algorithm:\n- Performance unavailable: {err}")
                continue
            order_matrix = np.array(order_matrix)  # shape: [n_traj, n_periods]
            cost_matrix = np.array(cost_matrix)  # shape: [n_traj, n_periods, 2]
            n_traj, n_periods = order_matrix.shape
            # Compute total cost per trajectory
            traj_total_cost = np.sum(cost_matrix[:, :, 0] + cost_matrix[:, :, 1], axis=1)

            # Select representative trajectories: min, median, max cost
            sorted_indices = np.argsort(traj_total_cost)
            selected_indices = [
                sorted_indices[0],
                sorted_indices[len(sorted_indices) // 2],
                sorted_indices[-1],
            ][:n_sample]

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
                summary.append(f"    Costs: {costs.tolist()}")
            summaries.append("\n".join(summary))
        return "\n".join(summaries)

    def _get_processed(self, indivs):
        summaries = []
        for i, indiv in enumerate(indivs, start=1):
            order_matrix, cost_matrix, err = self._get_eval_matrices(indiv)
            if err is not None:
                summaries.append(f"\nNo.{i} policy:\n- Performance unavailable: {err}")
                continue
            order_matrix = np.array(order_matrix)  # shape: [n_traj, n_periods]
            cost_matrix = np.array(cost_matrix)  # shape: [n_traj, n_periods, 2]

            holding_costs = cost_matrix[:, :, 0]
            lostsale_costs = cost_matrix[:, :, 1]
            total_costs = holding_costs + lostsale_costs

            mean_total = np.mean(total_costs)
            std_total = np.std(total_costs)
            mean_holding = np.mean(holding_costs)
            mean_lostsale = np.mean(lostsale_costs)

            traj_total = np.sum(total_costs, axis=1)
            traj_mean = np.mean(traj_total)
            traj_std = np.std(traj_total)
            traj_min = np.min(traj_total)
            traj_max = np.max(traj_total)

            if self.version == 'v1':
                summaries.append(f"""
    No.{i} algorithm:
    - Average total cost per period = {mean_total:.2f} (std={std_total:.2f})
    - Average holding cost per period = {mean_holding:.2f}
    - Average lost-sale cost per period = {mean_lostsale:.2f}
    - Ratio holding : lost-sale = {mean_holding:.1f} : {mean_lostsale:.1f}
    - Per-trajectory total cost summary: mean = {traj_mean:.2f}, std={traj_std:.2f}, range=({traj_min:.2f}, {traj_max:.2f})
            """)
            else:
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
        return "\n".join(summaries)
