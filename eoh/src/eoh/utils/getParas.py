
class Paras():
    def __init__(self):
        #####################
        ### General settings  ###
        #####################
        self.method = 'eoh'
        self.problem = 'inventory'
        self.selection = None
        self.management = None

        #####################
        ### Self defined ###
        #####################
        self.n_train = 50
        self.exp_create_initial = False
        self.external_optimizer = 'scipy'
        self.iter_opt = 20
        self.param_loc = 'default'
        self.repeat = 0
        self.filename = 'res'
        self.store_option = 'append'
        self.algo_performance = 'plain'
        self.data_summary = 'no'

        #####################
        ### Self defined for Inventory ###
        #####################
        self.demand = 80
        self.dist = 'poisson'
        self.volatility = 'low'


        #####################
        ### Self defined for TSP ###
        #####################
        self.option = 'stochastic'
        self.n_node = 50



        #####################
        ###  EC settings  ###
        #####################
        self.ec_pop_size = 30  # number of algorithms in each population, default = 10
        self.ec_n_pop = 10 # number of populations, default = 10
        self.ec_operators = None # evolution operators: ['e1','e2','m1','m2'], default =  ['e1','e2','m1','m2']
        self.ec_m = 2  # number of parents for 'e1' and 'e2' operators, default = 2
        self.ec_operator_weights = None  # weights for operators, i.e., the probability of use the operator in each iteration, default = [1,1,1,1]
        
        #####################
        ### LLM settings  ###
        #####################
        self.llm_use_local = False  # if use local model
        self.llm_local_url = None  # your local server 'http://127.0.0.1:11012/completions'
        self.llm_api_endpoint = None # endpoint for remote LLM, e.g., api.deepseek.com
        self.llm_api_key = None  # API key for remote LLM, e.g., sk-xxxx
        self.llm_model = None  # model type for remote LLM, e.g., deepseek-chat

        #####################
        ###  Exp settings  ###
        #####################
        self.exp_debug_mode = False  # if debug
        self.exp_output_path = "./results0"
        self.exp_use_seed = False
        self.exp_seed_path = "./seeds/seeds.json"
        self.exp_use_continue = True
        self.exp_continue_id = 0
        self.exp_continue_path = "results/pops/initial_pool.json"
        self.exp_n_proc = 1
        
        #####################
        ###  Evaluation settings  ###
        #####################
        self.eva_timeout = 60
        self.eva_numba_decorator = False


    def set_parallel(self):
        import multiprocessing
        num_processes = multiprocessing.cpu_count()
        if self.exp_n_proc == -1 or self.exp_n_proc > num_processes:
            self.exp_n_proc = num_processes
            print(f"Set the number of proc to {num_processes} .")
    
    def set_ec(self):    
        
        if self.management == None:
            if self.method in ['ael','eoh']:
                self.management = 'pop_greedy'
            elif self.method == 'ls':
                self.management = 'ls_greedy'
            elif self.method == 'sa':
                self.management = 'ls_sa'
        
        if self.selection == None:
            self.selection = 'prob_rank'
        
        if self.ec_operators == None:
            if self.method == 'eoh':
                # self.ec_operators  = ['e1','e2','m1','m2']
                self.ec_operators = ['e1', 'e2', 'm2']
            # elif self.method == 'ael':
            #     self.ec_operators  = ['crossover','mutation']
            # elif self.method == 'ls':
            #     self.ec_operators  = ['m1']
            # elif self.method == 'sa':
            #     self.ec_operators  = ['m1']

        if self.ec_operator_weights == None:
            self.ec_operator_weights = [1 for _ in range(len(self.ec_operators))]
        elif len(self.ec_operator) != len(self.ec_operator_weights):
            print("Warning! Lengths of ec_operator_weights and ec_operator shoud be the same.")
            self.ec_operator_weights = [1 for _ in range(len(self.ec_operators))]
                    
        # if self.method in ['ls','sa'] and self.ec_pop_size >1:
        #     self.ec_pop_size = 1
        #     self.exp_n_proc = 1
        #     print("> single-point-based, set pop size to 1. ")
            
    def set_evaluation(self):
        # Initialize evaluation settings
        if self.problem == 'bp_online':
            self.eva_timeout = 20
            self.eva_numba_decorator  = True
        elif self.problem == 'tsp_construct':
            self.eva_timeout = 20
        elif self.problem == 'tsp':
            self.eva_timeout = 180
        elif self.problem == 'inventory2':
            self.eva_timeout = 180

                
    def set_paras(self, *args, **kwargs):
        
        # Map paras
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
              
        # Identify and set parallel 
        self.set_parallel()
        
        # Initialize method and ec settings
        self.set_ec()
        
        # Initialize evaluation settings
        self.set_evaluation()




if __name__ == "__main__":

    # Create an instance of the Paras class
    paras_instance = Paras()

    # Setting parameters using the set_paras method
    paras_instance.set_paras(llm_use_local=True, llm_local_url='http://example.com', ec_pop_size=8)

    # Accessing the updated parameters
    print(paras_instance.llm_use_local)  # Output: True
    print(paras_instance.llm_local_url)  # Output: http://example.com
    print(paras_instance.ec_pop_size)    # Output: 8
            
            
            
