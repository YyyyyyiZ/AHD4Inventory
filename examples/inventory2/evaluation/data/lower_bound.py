import numpy as np
from scipy.stats import poisson, norm
import json

def get_data(file_path, n_traj):
    instances = []
    with open(file_path, 'r') as f:
        data = json.load(f)
        for item in data:
            instances.append(item['demand'])
    if n_traj is not None:
        final_instances = instances[:n_traj]
    else:
        final_instances = instances
    return final_instances


h, p = 2, 10
lam = 80
mu, sigma = 80,20
alpha = p / (p + h)



trajectories = get_data("poisson1_test_80_low.json",50)
q_star = int(poisson.ppf(alpha, lam))



# trajectories = get_data("normal1_train_80_low.json",50)
# q_star = norm.ppf(alpha, loc=mu, scale=sigma)


def period_cost(q, d, h, p):
    return h * max(q - d, 0) + p * max(d - q, 0)


all_costs = []
for traj in trajectories:
    costs = [period_cost(q_star, d, h, p) for d in traj]
    all_costs.append(sum(costs))


avg_total_cost = np.mean(all_costs)
avg_period_cost = np.mean([c for traj in trajectories
                             for c in [period_cost(q_star, d, h, p) for d in traj]])

print(f"Optimal order quantity q* = {q_star}")
print(f"Trajectory costs = {all_costs}")
print(f"Average total cost over trajectories = {avg_total_cost:.2f}")
print(f"Average per-period cost over all trajectories = {avg_period_cost:.2f}")