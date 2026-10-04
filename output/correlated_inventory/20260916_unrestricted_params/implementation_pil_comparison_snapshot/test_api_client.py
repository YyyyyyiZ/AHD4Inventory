import concurrent.futures
import tempfile
import unittest

from .api_client import BudgetedClient, BudgetExceeded


class TestBudget(unittest.TestCase):
    def test_parallel_reservations_and_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            client = BudgetedClient(folder, limit_usd=.01)
            def reserve(i):
                try:
                    client._reserve(str(i), [{"role": "user", "content": "hi"}], 4096, {})
                    return True
                except BudgetExceeded:
                    return False
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                successes = list(pool.map(reserve, range(16)))
            self.assertEqual(sum(successes), 1)
            summary = BudgetedClient(folder, limit_usd=.01).summary()
            self.assertLessEqual(summary["committed_upper_usd"], .01)
            self.assertGreater(summary["held_upper_usd"], 0)

    def test_unknown_charge_retained_rejection_releases(self):
        with tempfile.TemporaryDirectory() as folder:
            client = BudgetedClient(folder, limit_usd=1)
            upper = client._reserve("a", [{"role": "user", "content": "hi"}], 100, {})
            client._finish("a", "unknown_charge")
            self.assertEqual(client.summary()["held_upper_usd"], upper)
            client._reserve("b", [{"role": "user", "content": "hi"}], 100, {})
            client._finish("b", "rejected", actual_cost_usd=0)
            self.assertEqual(client.summary()["held_upper_usd"], upper)
            client._reserve("c", [{"role": "user", "content": "hi"}], 100, {})
            client._finish("c", "complete", actual_cost_usd=.00002)
            self.assertAlmostEqual(client.summary()["committed_upper_usd"], upper+.00002)


if __name__ == "__main__":
    unittest.main()
