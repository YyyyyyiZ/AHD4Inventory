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
        self.n_horizon = 2
        self.exp_create_initial = False
        self.external_optimizer = 'scipy'
        self.iter_opt = 20
        self.param_loc = 'default'
        self.param_num = 0
        self.repeat = 0
        self.filename = 'res'
        self.algo_performance = 'plain'
        self.data_summary = 'no'

        #####################
        ### Self defined for Inventory ###
        #####################
        self.dist = 'normal_std30_L6_c1_5'
        self.order_option = 'order_before_sell'
        self.prompt_version = 'v2'  # 'v1' = old version, 'v2' = new version
        self.prompt_with_explanations = False

        # #####################
        # ### Self defined for TSP ###
        # #####################
        # self.option = 'stochastic'
        # self.n_node = 50

        #####################
        ###  EC settings  ###
        #####################
        self.ec_pop_size = 30  # number of algorithms in each population, default = 10
        self.ec_n_pop = 10  # number of populations, default = 10
        self.ec_operators = None  # evolution operators: ['e1','e2','m1','m2'], default =  ['e1','e2','m1','m2']
        self.ec_m = 2  # number of parents for 'e1' and 'e2' operators, default = 2
        self.ec_operator_weights = None  # weights for operators, i.e., the probability of use the operator in each iteration, default = [1,1,1,1]

        #####################
        ### LLM settings  ###
        #####################
        self.llm_use_local = False  # if use local model
        self.llm_local_url = None  # your local server 'http://127.0.0.1:11012/completions'
        self.llm_api_endpoint = None  # kept for compatibility; remote LLM is routed via OpenRouter
        self.llm_api_key = None  # remote LLM API key (prefer OPENROUTER_API_KEY)
        self.llm_model = None  # OpenRouter model id, e.g., deepseek/deepseek-chat-v3-0324

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
            self.management = 'pop_greedy'

        if self.selection == None:
            self.selection = 'best_deterministic'

        if self.ec_operators == None:
            self.ec_operators = ['e1', 'e2', 'm2']

        if self.ec_operator_weights == None:
            self.ec_operator_weights = [1 for _ in range(len(self.ec_operators))]
        elif len(self.ec_operator) != len(self.ec_operator_weights):
            print("Warning! Lengths of ec_operator_weights and ec_operator shoud be the same.")
            self.ec_operator_weights = [1 for _ in range(len(self.ec_operators))]


    def set_evaluation(self):
        # Initialize evaluation settings
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
