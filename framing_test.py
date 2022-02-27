import unittest

from pandas import DataFrame

import account
import framing
import investment
import mock
import pandas as pd
import numpy as np


class ContextTest(unittest.TestCase):

    def setUp(self):
        fidelity_account = mock.MagicMock(account.Account, autospect=True)
        fidelity_account.name = 'Joint WROS'
        fidelity_account.institution = 'Fidelity'
        fidelity_account.account_file = 'Fidelity_Positions.csv'
        fidelity_account.is_taxable = True
        fidelity_account.holdings = [
            investment.Investment('CRISX', investment.AssetClass.SMALL_CAP, 'Small Cap Value Fund Class Institutional',
                                  500, share_price=10),
            investment.Investment('FSKAX', investment.AssetClass.CORE_US, 'Fidelity Total Market Index', 1000,
                                  share_price=10),
            investment.Investment('CASH', investment.AssetClass.CASH, 'Money Market', 5000,
                                  share_price=1)
        ]
        fidelity_account.options = [holding.fund for holding in fidelity_account.holdings]
        vanguard_account = mock.MagicMock(account.Account, autospec=True)
        vanguard_account.name = 'INDIVIDUAL IRA'
        vanguard_account.institution = 'Vanguard'
        vanguard_account.account_file = 'Vanguard_Positions.csv'
        vanguard_account.is_taxable = False
        vanguard_account.holdings = [
            investment.Investment('VNQ', investment.AssetClass.REAL_ESTATE, 'Vanguard Real Estate Index Fund', 2000,
                                  share_price=10)
        ]
        vanguard_account.options = [holding.fund for holding in vanguard_account.holdings]
        self._accounts = [fidelity_account, vanguard_account]
        portfolio_dict = {'account_name': ['Joint WROS', 'Joint WROS', 'Joint WROS', 'INDIVIDUAL IRA'],
                          'institution': ['Fidelity', 'Fidelity', 'Fidelity', 'Vanguard'],
                          'fund_name': ['Small Cap Value Fund Class Institutional', 'Fidelity Total Market Index',
                                        'Money Market', 'Vanguard Real Estate Index Fund'],
                          'asset_class': [investment.AssetClass.SMALL_CAP, investment.AssetClass.CORE_US,
                                          investment.AssetClass.CASH, investment.AssetClass.REAL_ESTATE],
                          'ticker_symbol': ['CRISX', 'FSKAX', 'CASH', 'VNQ'],
                          'share_price': [10, 10, 1, 10],
                          'num_shares': [500, 1000, 5000, 2000],
                          'value': [5000, 10000, 5000, 20000]}
        self._df = pd.DataFrame(portfolio_dict)

    def test_taxable_getter(self):
        cash_allocation_strategy = framing.CashAllocationStrategy()
        framing_context = framing.Context(taxable=cash_allocation_strategy)
        self.assertEqual(framing_context.taxable, cash_allocation_strategy)

    def test_taxable_setter(self):
        framing_context = framing.Context()
        cash_allocation_strategy = framing.CashAllocationStrategy()
        framing_context.taxable = cash_allocation_strategy
        self.assertEqual(framing_context.taxable, cash_allocation_strategy)

    def test_non_taxable_getter(self):
        rebalance_allocation_strategy = framing.RebalanceAllocationStrategy()
        framing_context = framing.Context(non_taxable=rebalance_allocation_strategy)
        self.assertEqual(framing_context.non_taxable, rebalance_allocation_strategy)

    def test_non_taxable_setter(self):
        framing_context = framing.Context()
        rebalance_allocation_strategy = framing.RebalanceAllocationStrategy()
        framing_context.non_taxable = rebalance_allocation_strategy
        self.assertEqual(framing_context.non_taxable, rebalance_allocation_strategy)

    def test_get_initial_allocation_no_strategy(self):
        expected_allocation = np.zeros(len(self._df.index))
        framing_context = framing.Context()
        initial_allocation = framing_context.get_initial_allocation(self._df, self._accounts)
        self.assertCountEqual(initial_allocation, expected_allocation)

    def test_get_initial_allocation_taxable_strategy(self):
        expected_allocation = np.zeros(len(self._df.index))
        expected_allocation[1] = 500
        expected_allocation[2] = -5000
        framing_context = framing.Context(taxable=framing.CashAllocationStrategy())
        initial_allocation = framing_context.get_initial_allocation(self._df, self._accounts)
        self.assertCountEqual(initial_allocation, expected_allocation)

    def test_get_initial_allocation_non_taxable_strategy(self):
        expected_allocation = np.zeros(len(self._df.index))
        framing_context = framing.Context(non_taxable=framing.RebalanceAllocationStrategy())
        initial_allocation = framing_context.get_initial_allocation(self._df, self._accounts)
        self.assertCountEqual(initial_allocation, expected_allocation)

    def test_get_allocation_bounds_no_strategy(self):
        expected_bounds = [(0, framing._JITTER)] * len(self._df.index)
        framing_context = framing.Context()
        bounds = framing_context.get_allocation_bounds(self._df, self._accounts)
        self.assertCountEqual(bounds, expected_bounds)

    def test_get_allocation_bounds_taxable_strategy(self):
        expected_bounds = [(0, framing._JITTER)] * len(self._df.index)
        expected_bounds[0] = (0, 5000/10)
        expected_bounds[1] = (0, 5000/10)
        expected_bounds[2] = (-5000, -5000 + framing._JITTER)
        framing_context = framing.Context(taxable=framing.CashAllocationStrategy())
        allocation_bounds = framing_context.get_allocation_bounds(self._df, self._accounts)
        self.assertCountEqual(allocation_bounds, expected_bounds)

    def test_get_allocation_bounds_non_taxable_strategy_single_holding(self):
        expected_bounds = [(0, framing._JITTER)] * len(self._df.index)
        framing_context = framing.Context(non_taxable=framing.RebalanceAllocationStrategy())
        allocation_bounds = framing_context.get_allocation_bounds(self._df, self._accounts)
        self.assertCountEqual(allocation_bounds, expected_bounds)

    def test_get_allocation_bounds_non_taxable_strategy_multiple_holdings(self):
        add_holding = {'account_name': 'INDIVIDUAL IRA',
                        'institution': 'Vanguard',
                        'fund_name': 'Vanguard Emerging Markets Index Fund',
                        'asset_class': investment.AssetClass.EMERGING_MARKETS,
                        'ticker_symbol': 'VWD',
                        'share_price': 10,
                        'num_shares': 1000,
                        'value': 10000}
        self._df = self._df.append(add_holding, ignore_index=True)
        expected_bounds = [(0, framing._JITTER)] * len(self._df.index)
        expected_bounds[3] = (-2000, 1000)
        expected_bounds[4] = (-1000, 2000)
        framing_context = framing.Context(non_taxable=framing.RebalanceAllocationStrategy())
        allocation_bounds = framing_context.get_allocation_bounds(self._df, self._accounts)
        self.assertCountEqual(allocation_bounds, expected_bounds)


if __name__ == '__main__':
    unittest.main()
