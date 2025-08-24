import numpy as np
import pickle

def generate_deterministic_instances(n_instance=3, n_cities=5, factor=1.0, seed=2025, save_file="deterministic.json"):
    np.random.seed(seed)
    all_instances = []

    for inst_id in range(n_instance):
        # 坐标范围缩放
        coordinates = np.random.rand(n_cities, 2) * factor
        distances = np.linalg.norm(np.array(coordinates)[:, np.newaxis] - np.array(coordinates), axis=2)

        all_instances.append({
            "instance_id": inst_id,
            "n_cities": n_cities,
            "coordinates": coordinates,
            "distances": distances
        })

    with open(save_file, "wb") as f:
        # json.dump(all_instances, f, indent=2)
        pickle.dump(all_instances, f)

    return all_instances


def generate_stochastic_instances(n_instance=5, n_cities=5, std=0.05, factor=1.0, seed=2025, save_file="stochastic.json"):
    np.random.seed(seed)

    # Shared coordinates
    coordinates = np.random.rand(n_cities, 2) * factor
    base_distances = np.linalg.norm(np.array(coordinates)[:, np.newaxis] - np.array(coordinates), axis=2)

    all_instances = []
    for inst_id in range(n_instance):
        if std > 0:
            noise = np.random.normal(0, std*factor, size=base_distances.shape)
            noisy_distances = np.maximum(0, (base_distances + noise + noise.T) / 2)
        else:
            noisy_distances = base_distances

        all_instances.append({
            "instance_id": inst_id,
            "n_cities": n_cities,
            "coordinates": coordinates,
            "distances": noisy_distances
        })

    with open(save_file, "wb") as f:
        pickle.dump(all_instances, f)
        # json.dump(all_instances, f, indent=2)

    return all_instances

n_cities=50
factor=50
mode='train'
n_instance=100

generate_deterministic_instances(
    n_instance=n_instance, n_cities=n_cities, factor=factor, save_file=f"data/{mode}_deterministic_{n_cities}.pkl"
)
generate_stochastic_instances(
    n_instance=n_instance, n_cities=n_cities, std=0.05, factor=factor, save_file=f"data/{mode}_stochastic_{n_cities}.pkl"
)

mode='test'
n_instance=10
generate_deterministic_instances(
    n_instance=n_instance, n_cities=n_cities, factor=factor, save_file=f"data/{mode}_deterministic_{n_cities}.pkl"
)
generate_stochastic_instances(
    n_instance=n_instance, n_cities=n_cities, std=0.05, factor=factor, save_file=f"data/{mode}_stochastic_{n_cities}.pkl"
)






