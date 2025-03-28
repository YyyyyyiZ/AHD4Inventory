# example heuristic
# replace it with your own heuristic designed by EoH
# import numpy as np
# def select_next_node(current_node, destination_node, unvisited_nodes, distance_matrix):
#     next_node_id = np.argmin([distance_matrix[current_node][i] for i in unvisited_nodes if i != current_node])
#     next_node = unvisited_nodes[next_node_id]
#     return next_node
#

import numpy as np

def select_next_node(current_node, destination_node, unvisited_nodes, distance_matrix):
    max_ratio = -float('inf')
    next_node = None

    for node in unvisited_nodes:
        if distance_matrix[current_node, node] == 0:
            continue
        ratio = distance_matrix[current_node, destination_node] / distance_matrix[current_node, node]
        if ratio > max_ratio:
            max_ratio = ratio
            next_node = node
    return next_node
