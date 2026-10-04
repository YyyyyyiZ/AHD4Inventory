"""Numerical contract checks independent of generated policies or paid models."""
import ast
from pathlib import Path
import unittest
import numpy as np
from .environment import step, evaluate, baseline_costs, summarize


class ContractTests(unittest.TestCase):
    def test_hand_calculated_cost_and_pipeline(self):
        nxt, parts=step([5,5,5,5,5],3,6.25)
        np.testing.assert_allclose(nxt,[3.75,5,5,5,3])
        np.testing.assert_allclose(parts,[27.075,3.75,0,0,0])
        # Excess demand is charged backlog AND lost-sale penalties, while
        # the carried backlog itself is capped at ten.
        nxt,parts=step([-9,1,2,3,4],2,10)
        np.testing.assert_allclose(nxt,[-10,2,3,4,2])
        np.testing.assert_allclose(parts,[18.05,0,36,0,8000])
        nxt,parts=step([5,5,5,5,5],0,0)
        np.testing.assert_allclose(parts,[0,5,0,40,0])

    def test_rounding_is_observation_only(self):
        observed=[]
        def policy(s):
            observed.append(s)
            return 0
        parts=evaluate(policy,np.array([[6.25,0.0]]))
        self.assertEqual(observed,[(5,5,5,5,5),(4,5,5,5,0)])
        # The second disposal cost uses 3.75, not the observed integer 4.
        self.assertAlmostEqual(parts.sum(),3.75+0.95*(5+8*3.75))

    def test_order_becomes_available_after_four_transitions(self):
        s=np.zeros(5)
        for k in range(4):
            s,parts=step(s,7 if k==0 else 0,0)
            if k<3: self.assertEqual(s[:2].sum(),0)
        np.testing.assert_array_equal(s,[0,7,0,0,0])

    def test_batch_reference_matches_scalar_with_rounded_observation(self):
        d=np.array([[6.25,9.1,0.,3.7,10.],[0.,2.2,3.3,4.4,9.9]])
        candidates=[("constant",3),("base_stock",23)]
        actual=baseline_costs(d,candidates)
        a=evaluate(lambda s:3,d).sum(axis=1)
        b=evaluate(lambda s:min(10,max(0,23-sum(s))),d).sum(axis=1)
        np.testing.assert_allclose(actual,np.column_stack([a,b]),rtol=1e-14)

    def test_invalid_actions_not_repaired(self):
        for action in [-1,11,1.5,float("nan"),True]:
            with self.assertRaises(ValueError): step([5]*5,action,3)

    def test_statistics_use_paths_and_sample_variance(self):
        result=summarize([10,20,30])
        self.assertEqual(result["mean"],20)
        self.assertAlmostEqual(result["standard_error"],10/np.sqrt(3))

    def test_original_source_parity(self):
        from .experiment import RUN
        path=RUN/"source/MDP__PIC__perishableInventory.py"
        source=ast.parse(path.read_text())
        names={"get_cost_given_noise","get_next_state_given_noise"}
        functions=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name in names]
        self.assertEqual(len(functions),2)
        for f in functions: f.decorator_list=[]
        ns={"np":np}
        exec(compile(ast.Module(body=functions,type_ignores=[]),str(path),"exec"),ns)
        rng=np.random.default_rng(789)
        for _ in range(1000):
            state=rng.uniform(0,10,5); state[0]=rng.uniform(-10,10)
            q=int(rng.integers(11)); d=float(rng.uniform(0,10))
            nxt,parts=step(state,q,d)
            reference=ns["get_cost_given_noise"](9.025,1,2,8,1000,-10,2,state,q,d)
            reference_next=ns["get_next_state_given_noise"](5,-10,2,4,state,q,d)
            self.assertAlmostEqual(parts.sum(),reference,places=9)
            np.testing.assert_allclose(nxt,reference_next,rtol=0,atol=0)


if __name__=="__main__": unittest.main()
