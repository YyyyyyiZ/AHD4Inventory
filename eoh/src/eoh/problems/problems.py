class Probs():
    def __init__(self,paras):

        if not isinstance(paras.problem, str):
            self.prob = paras.problem
            print("- Prob local loaded ")
        elif paras.problem == "inventory2":
            from .optimization.inventory2 import run
            self.prob = run.INVENTORY(dist=paras.dist, demand=paras.demand, volatility=paras.volatility, n_train=paras.n_train)
            print("- Prob "+paras.problem+" loaded ")
        elif paras.problem == "tsp":
            from .optimization.tsp import run
            self.prob = run.TSP(option=paras.option, n_node=paras.n_node, n_train=paras.n_train)
            print("- Prob "+paras.problem+" loaded ")
        elif paras.problem == "tsp_construct":
            from .optimization.tsp_greedy import run
            self.prob = run.TSPCONST()
            print("- Prob "+paras.problem+" loaded ")
        elif paras.problem == "bp_online":
            from .optimization.bp_online import run
            self.prob = run.BPONLINE()
            print("- Prob "+paras.problem+" loaded ")
        else:
            print("problem "+paras.problem+" not found!")


    def get_problem(self):
        return self.prob
