"""Train-only prompts for the unchanged m2 evolutionary search operator."""
from __future__ import annotations

import json
import numpy as np


class GetPrompts:
    def __init__(self, scenario, burnin=500, horizon=200):
        self.scenario = scenario
        self.burnin, self.horizon = int(burnin), int(horizon)

    def get_task(self):
        s = self.scenario
        law = f"Demand has a stationary continuous Exponential marginal with mean {s.mean_demand}; no rounding. "
        if s.demand_process == 'iid':
            law += "Demands are independent over time and across paths. "
        elif s.demand_process == 'ar1':
            law += (f"The known generator is Z_t = {s.rho_latent}*Z_(t-1) + sqrt(1-{s.rho_latent}^2)*epsilon_t, "
                    "epsilon_t iid standard Normal, with stationary Z initially standard Normal. "
                    f"D_t = -{s.mean_demand}*log(1-Phi(Z_t)), where Phi is the standard Normal CDF. "
                    f"The previous latent Z can be inferred from last_demand as Phi_inverse(1-exp(-last_demand/{s.mean_demand})). "
                    "The current Z and future innovations are not observed; rho is latent Gaussian correlation, not demand Pearson correlation. ")
        else:
            law += (f"The known generator has S_t in {{0,1}}, with P(S_t=S_(t-1))={s.regime_p_stay}, "
                    "stationary P(S=0)=P(S=1)=0.5, and independent V_t uniform(0,1). "
                    f"U_t=(S_t+V_t)/2 and D_t=-{s.mean_demand}*log(1-U_t). "
                    f"Previous regime S_(t-1) is identified by last_demand >= {s.mean_demand}*log(2). "
                    "The current regime and V_t are not observed before ordering. ")
        return (
            "Design a deterministic stationary lost-sales inventory policy. At each period: "
            "receive all orders due now; observe the current lead-time quotation; order; observe "
            "demand and sell; pay holding cost on remaining inventory and lost-sales cost on unmet demand. "
            "An order placed now with quoted_lead_time l arrives exactly l periods later. Orders may overtake. "
            "on_hand_inventory ALREADY includes today's arrivals. pipeline_orders[k-1] is the total "
            f"OLD quantity arriving k periods from now, for k=1,...,{s.max_lead_time-1}; its length is "
            f"{s.max_lead_time-1}. It excludes today's arrivals and today's new order. "
            "last_demand is the previous period's FULL realized demand, including unmet demand; "
            "quoted_lead_time is known before ordering. Do not observe current/future demand or latent state. "
            "All quantities and orders are nonnegative finite real numbers; there is no order capacity or order fee. "
            f"Holding cost is {s.holding_cost}, lost-sales cost {s.lost_sales_cost}. "
            f"Lead-time support is {list(s.lead_time_values)}, probabilities {list(s.lead_time_probabilities)}. "
            f"The simulator starts empty, runs {self.burnin} ordinary demand periods as unscored burn-in, "
            f"then scores {self.horizon} periods. There are NO zero-demand preparation periods. "
            "Optimize average total scored cost on the supplied training trajectories. The policy has no time "
            "argument and must apply the same state rule in burn-in and scoring. "
            "All compared methods receive these same generator parameters; the training summaries provide additional sample diagnostics. "
            + law + "\n"
        )

    def get_func_name(self):
        return "compute_order_amount"

    def get_func_inputs(self):
        return ["on_hand_inventory", "pipeline_orders", "last_demand", "quoted_lead_time"]

    def get_func_outputs(self):
        return ["order_amount"]

    def get_inout_inf(self):
        return (
            "Inputs: on_hand_inventory float, pipeline_orders one-dimensional float64 array, "
            "last_demand float, quoted_lead_time int. Return one finite nonnegative float named order_amount. "
            "Use all four arguments in the function signature; unused arguments are allowed.\n"
        )

    def get_other_inf(self):
        return (
            "Only import math and/or numpy. Supply one function named compute_order_amount, with exactly "
            "the four named positional arguments. Use numerical arithmetic, bounded for-loops, if/else, "
            "and Numba-compatible math/NumPy operations. Do not use decorators, helper functions, recursion, "
            "randomness, files, networking, dynamic evaluation, printing, exception handling, or global state. "
            "Do not mutate pipeline_orders. Declare every OPT_PARAM as a simple numeric assignment INSIDE "
            "the function, on its own line with the OPT_PARAM dictionary comment. A maximum of four such "
            "parameters is allowed. Return the variable order_amount, with a single final return statement.\n"
        )


M2_TEMPLATE = """{prompt_task}
{data_summary}

Modify the following historical policy to lower its average cumulative TRAINING cost. Keep its useful
structure or replace parts when the observed training performance suggests a better state rule.
{external_optimizer}
The policy must be strictly stationary: its action may depend only on the four current arguments
on_hand_inventory, pipeline_orders, last_demand, quoted_lead_time and fixed numerical coefficients.
No clocks, episode indexes, past calls, caches, mutable globals, or function attributes.
{prompt_inout_inf}
{prompt_other_inf}

Historical policy:
{algo_code}

Training performance (only the scored window after burn-in):
{algo_performance}

Return Python code followed by a concise explanation inside double curly braces, such as
{{{{Changed the target and response to the previous demand.}}}}. Do not provide other text.
"""


class TrainingAnalyzer:
    """All summaries derive exclusively from the supplied training tapes."""
    def __init__(self, problem, *args, **kwargs):
        self.prob = problem
        self.param = ""
        self._summary = None

    def get_data_summary(self):
        if self._summary is not None:
            return self._summary
        p = self.prob
        # Correlation needs within-path adjacent pairs, never a concatenation boundary.
        demand = p.train_tapes["demands"][:, :p.burnin+p.horizon]
        scored = demand[:, p.burnin:]
        quantiles = np.quantile(scored, [.1, .25, .5, .75, .9, .99])
        autocorrelations = {}
        for lag in (1, 2, 5, 10):
            if demand.shape[1] > lag:
                x, y = demand[:, :-lag].ravel(), demand[:, lag:].ravel()
                autocorrelations[str(lag)] = (float(np.corrcoef(x, y)[0, 1])
                                               if x.std() > 0 and y.std() > 0 else 0.)
        x, y = demand[:, :-1].ravel(), demand[:, 1:].ravel()
        cuts = np.quantile(x, [0, .25, .5, .75, 1])
        conditional = []
        for i in range(4):
            mask = (x >= cuts[i]) & ((x <= cuts[i+1]) if i == 3 else (x < cuts[i+1]))
            conditional.append({"previous_demand_range": [round(float(cuts[i]), 3), round(float(cuts[i+1]), 3)],
                                "mean_next_demand": round(float(y[mask].mean()), 3) if mask.any() else None})
        values = {"training_paths": len(demand), "burnin_periods": p.burnin, "scored_periods": p.horizon,
                  "scored_demand_mean": round(float(scored.mean()), 4),
                  "scored_demand_std": round(float(scored.std()), 4),
                  "scored_demand_quantiles_10_25_50_75_90_99": np.round(quantiles, 3).tolist(),
                  "within_path_demand_autocorrelation": {k: round(v, 4) for k, v in autocorrelations.items()},
                  "conditional_next_demand": conditional,
                  "illustrative_scored_demand_sequences": np.round(scored[:3, :20], 2).tolist()}
        self._summary = ("Training-only compact diagnostics accompanying the known generator stated above. "
                         "Burn-in observations may estimate dependence; performance costs exclude burn-in.\n"
                         + json.dumps(values, ensure_ascii=False, allow_nan=False))
        return self._summary

    def get_algo_performance(self, individuals):
        summaries = []
        for individual in individuals:
            costs = np.asarray(individual["cost_matrix"], dtype=float)
            orders = np.asarray(individual["order_matrix"], dtype=float)
            if costs.shape != (len(self.prob.train_tapes["demands"]), self.prob.horizon, 2):
                raise ValueError("Feedback cost matrix must contain only the scored training window")
            totals = costs.sum(axis=(1, 2))
            summaries.append({"mean_total_cost": float(totals.mean()),
                              "mean_cost_per_scored_period": float(costs.sum(axis=2).mean()),
                              "mean_holding_per_scored_period": float(costs[:, :, 0].mean()),
                              "mean_lost_sales_per_scored_period": float(costs[:, :, 1].mean()),
                              "std_total_cost_across_training_paths": float(totals.std()),
                              "mean_order": float(orders.mean()),
                              "order_quantiles_10_50_90": np.quantile(orders, [.1, .5, .9]).tolist(),
                              "scored_paths": len(totals), "scored_periods": self.prob.horizon})
        return json.dumps(summaries, ensure_ascii=False, allow_nan=False)
