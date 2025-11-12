import numpy as np
import json
import os
from datetime import datetime
import glob


def generate_random_instance(dist='poisson',num_periods=50, lead_time=1, demand_mean = 50,  initial_inventory=80,
                             holding_cost=2, lost_sales_cost=10, volatility='median', instance_id=None):
    """
    Generate a random inventory problem instance.
    Args:
        num_periods (int): Number of simulation periods (default: 30).
        demand_mean (float)
        holding_cost (float)
        lost_sales_cost (float)
        volatility: 'low', 'median', or 'high' to control demand variability
        instance_id (str): Unique identifier for the instance (auto-generated if None).
    Returns:
        dict: Randomly generated instance parameters.
    """
    # Random initial inventory (50-150 units)
    if initial_inventory is None:
        initial_inventory = np.random.randint(60, 100)

    # Random demand (Poisson distribution, lambda=40-80)
    if demand_mean is None:
        demand_mean = np.random.randint(50, 80)

    # Adjust variance based on volatility level
    if volatility == 'low' and dist == 'poisson':
        # For low volatility, keep variance close to mean (like Poisson)
        demand = np.random.poisson(demand_mean, size=num_periods)
    elif volatility == 'low' and dist == 'normal':
        # For low volatility, keep variance close to mean (like Poisson)
        demand = np.random.normal(demand_mean, scale=10, size=num_periods)
    elif volatility == 'high':
        # For high volatility, increase variance relative to mean
        # Using negative binomial which allows overdispersion
        # We set variance = 2*mean (can adjust this factor)
        p = demand_mean / (2 * demand_mean)  # p = mean/variance
        demand = np.random.negative_binomial(demand_mean, p, size=num_periods)
    else:  # 'median'
        # For medium volatility, moderate increase in variance
        # Using negative binomial with variance = 1.5*mean
        p = demand_mean / (1.5 * demand_mean)
        demand = np.random.negative_binomial(demand_mean, p, size=num_periods)

        # Ensure mean stays exactly at demand_mean by scaling
    current_mean = np.mean(demand)
    demand = np.round(demand * (demand_mean / current_mean)).astype(int).tolist()


    # Auto-generate instance_id if not provided
    if instance_id is None:
        instance_id = f"instance_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return {
        'instance_id': instance_id,
        'initial_inventory': initial_inventory,
        'demand': demand,
        'num_periods': num_periods,
        'holding_cost': holding_cost,
        'lost_sales_cost': lost_sales_cost,
        'lead_time': lead_time
    }

def save_instances(instances, file_path):
    """
    Save a list of instances to a JSON file.
    Args:
        instances (list): List of instances to save.
        file_path (str): Path to the output JSON file.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(instances, f, indent=4)
    print(f"Saved {len(instances)} instances to {file_path}")



def load_instances(pattern):
    """
    Load instances from a JSON file.
    Args:
        file_path (str): Path to the JSON file.
    Returns:
        list: Loaded instances.
    """
    instances = []
    for file_path in glob.glob(pattern):
        with open(file_path, 'r') as f:
            data = json.load(f)
            if isinstance(data, list):  # If file contains a list of instances
                instances.extend(data)
            else:  # If file contains a single instance
                instances.append(data)
    return instances

if __name__ == "__main__":
    lead_time = 1
    num_periods = 50
    volatility = ['low']
    distribution = 'normal'
    # volatility = ['low', 'median', 'high']
    demands = [80]
    for vol in volatility:
        for demand_mean in demands:
            test_instances = [generate_random_instance(dist=distribution, num_periods=num_periods, lead_time=lead_time, demand_mean = demand_mean,
                                                       holding_cost=2, lost_sales_cost=10, volatility=vol,
                                                       instance_id=f"test_{i}") for i in range(500)]
            save_instances(test_instances, f"data/{distribution}1_test_{demand_mean}_{vol}.json")

            training_instances = [generate_random_instance(dist=distribution, num_periods=num_periods, lead_time=lead_time, demand_mean=demand_mean,
                                                           holding_cost=2, lost_sales_cost=10, volatility=vol,
                                                           instance_id=f"train_{i}") for i in range(100)]
            save_instances(training_instances, f"data/{distribution}1_train_{demand_mean}_{vol}.json")