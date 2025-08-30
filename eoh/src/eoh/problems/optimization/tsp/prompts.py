class GetPrompts():
    def __init__(self):
#         self.prompt_task = "Given a set of nodes with their coordinates, \
# you need to find the shortest route that visits each node once and returns to the starting node. \
# The task can be solved step-by-step by starting from the current node and iteratively choosing the next node. \
# Help me design a novel algorithm that is different from the algorithms in literature to select the next node in each step."
#         self.prompt_func_name = "select_next_node"
#         self.prompt_func_inputs = ["current_node", "destination_node", "univisited_nodes", "distance_matrix"]
#         self.prompt_func_outputs = ["next_node"]
#         self.prompt_inout_inf = "'current_node', 'destination_node', 'next_node', and 'unvisited_nodes' are node IDs. 'distance_matrix' is the distance matrix of nodes."
#         self.prompt_other_inf = "All are Numpy arrays."

        self.prompt_task = "Given a set of nodes with fixed coordinates, \
                the pairwise distances between nodes follow stochastic realizations. \
                Your goal is to construct a route that visits each node exactly once and returns to the starting node. \
                Design a novel algorithm—distinct from classical approaches in the literature—that adaptively selects the next node under uncertainty."

        self.prompt_func_name = "select_route"

        self.prompt_func_inputs = ["coordinate_matrix"]

        self.prompt_func_outputs = ["route"]

        self.prompt_inout_inf = """
                Inputs:
                - `coordinate_matrix` (numpy.ndarray of shape (n_nodes, 2)): The coordinates of all nodes.
        
                Output:
                - `route` (list of int): A sequence of node indices representing the tour, \
                  where the first and last elements are the starting node.
                """

        self.prompt_other_inf = ""


    def get_task(self):
        return self.prompt_task

    def get_func_name(self):
        return self.prompt_func_name

    def get_func_inputs(self):
        return self.prompt_func_inputs

    def get_func_outputs(self):
        return self.prompt_func_outputs

    def get_inout_inf(self):
        return self.prompt_inout_inf

    def get_other_inf(self):
        return self.prompt_other_inf


if __name__ == "__main__":
    getprompts = GetPrompts()
    print(getprompts.get_task())
