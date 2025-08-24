import numpy as np
import json
import pickle
import glob
import sys
import types
import warnings
from .prompts import GetPrompts


class TSP:
    def __init__(self,option='stochastic',n_node=50, n_train=50) -> None:
        self.ndelay = 1
        self.option = option
        self.n_node = n_node
        self.neighbor_size = np.minimum(50,self.n_node)
        self.running_time = 10

        self.mode = 'train'
        self.train_instances = self.load_instances(mode='train', n_traj=n_train)
        self.test_instances = self.load_instances(mode='test')

        self.prompts = GetPrompts()
    
    def load_instances(self, mode='train', n_traj=None):
        pattern = f"evaluation/data/{mode}_{self.option}_{self.n_node}.pkl"

        # Find all matching files and load their contents
        instances = []
        for file_path in glob.glob(pattern):
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, list):  # If file contains a list of instances
                    instances.extend(data)
                else:  # If file contains a single instance
                    instances.append(data)
        if n_traj is not None:
            final_instances = instances[:n_traj]
        else:
            final_instances = instances
        return final_instances

        

    def tour_cost(self,instance, solution, n_node):
        cost = 0
        for j in range(n_node - 1):
            cost += np.linalg.norm(instance[int(solution[j])] - instance[int(solution[j + 1])])
        cost += np.linalg.norm(instance[int(solution[-1])] - instance[int(solution[0])])
        return cost

    def generate_neighborhood_matrix(self,instance):
        instance = np.array(instance)
        n = len(instance)
        neighborhood_matrix = np.zeros((n, n), dtype=int)

        for i in range(n):
            distances = np.linalg.norm(instance[i] - instance, axis=1)
            sorted_indices = np.argsort(distances)  # sort indices based on distances
            neighborhood_matrix[i] = sorted_indices

        return neighborhood_matrix

    def evaluate_mode(self, eva, instances):
        dis = []
        node_matrix = []
        cost_matrix = []

        for instance in instances:
            neighbor_matrix = self.generate_neighborhood_matrix(instance['coordinates'])
            destination_node = 0
            current_node = 0

            route = np.zeros(self.n_node, dtype=int)
            route[0] = current_node

            step_nodes = [int(current_node)]
            step_costs = []

            for i in range(1, self.n_node - 1):
                near_nodes = neighbor_matrix[current_node][1:]
                mask = ~np.isin(near_nodes, route[:i])
                unvisited_near_nodes = near_nodes[mask]
                unvisited_near_size = np.minimum(self.neighbor_size, unvisited_near_nodes.size)
                unvisited_near_nodes = unvisited_near_nodes[:unvisited_near_size]

                next_node = eva.select_next_node(current_node, destination_node, unvisited_near_nodes,
                                                 instance['distances'])

                if next_node in route:
                    return {'avg': None,'trajectory': None,'order_matrix': None,'cost_matrix': None,}

                step_nodes.append(int(next_node))
                step_costs.append(float(instance['distances'][current_node][next_node]))

                current_node = next_node
                route[i] = current_node

            mask = ~np.isin(np.arange(self.n_node), route[:self.n_node - 1])
            last_node = np.arange(self.n_node)[mask][0]
            route[self.n_node - 1] = last_node

            step_nodes.append(int(last_node))
            step_costs.append(float(instance['distances'][current_node][last_node]))

            LLM_dis = self.tour_cost(instance['coordinates'], route, self.n_node)
            dis.append(LLM_dis)

            node_matrix.append(step_nodes)
            cost_matrix.append(step_costs)

        res = {
            'avg': np.average(dis),
            'trajectory': dis,
            'order_matrix': node_matrix,
            'cost_matrix': cost_matrix,
            'lower': 0.0,
            'upper': 0.0,
        }
        return res

    def greedy(self,eva):
        res_train = self.evaluate_mode(eva, self.train_instances)
        res_test = self.evaluate_mode(eva, self.test_instances)
        res_train['test_obj'] = res_test['avg']
        return res_train

    def evaluate(self, code_string):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            heuristic_module = types.ModuleType("heuristic_module")
            exec(code_string, heuristic_module.__dict__)
            sys.modules[heuristic_module.__name__] = heuristic_module
            fitness = self.greedy(heuristic_module)
            return fitness
            


