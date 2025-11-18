class Probs():
    def __init__(self,paras):

        if not isinstance(paras.problem, str):
            self.prob = paras.problem
            print("- Prob local loaded ")
        # elif paras.problem == "inventory2":
        #     from .optimization.inventory2 import run
        #     self.prob = run.INVENTORY(dist=paras.dist, demand=paras.demand, volatility=paras.volatility, n_train=paras.n_train)
        #     print("- Prob "+paras.problem+" loaded ")
        elif paras.problem == "inventory_ex" or paras.problem == "inventory2":
            from .optimization.inventory_ex import run
            self.prob = run.INVENTORY(dist=paras.dist, demand=paras.demand, volatility=paras.volatility, n_train=paras.n_train, n_horizon=paras.n_horizon,order_option=paras.order_option, prompt_version=paras.prompt_version)
            print("- Prob "+paras.problem+" loaded ")
        else:
            print("problem "+paras.problem+" not found!")


    def get_problem(self):
        return self.prob
