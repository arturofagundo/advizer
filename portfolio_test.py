# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import account
import allocation
import investment
import mock
import pandas as pd
import unittest
import portfolio


class BuildPortolioTest(unittest.TestCase):

    def setUp(self):
        self._account_desc = """
                             [
                                 {
                                    "institution": "Fidelity",
                                    "name": "Joint WROS",
                                    "filename": "Personal_Account_Positions.csv",
                                    "taxable": "True",
                                    "headers": {
                                      "name": "Account Name/Number",
                                      "symbol": "Symbol",
                                      "description": "Description",
                                      "num_shares": "Quantity",
                                      "share_price": "Last Price"
                                    }
                                 }
                            ]
                            """

    @mock.patch('account.Account')
    def test_build_portfolio(self, mock_account):
        test_account = mock.MagicMock(account.Account, autospect=True)
        test_account.name = 'Joint WROS'
        test_account.institution = 'Fidelity'
        test_account.account_file = 'Personal_Account_Positions.csv'
        test_account.is_taxable = True
        test_account.holdings = [
            investment.Investment('CRISX', 'Small Cap Value Fund Inst', 'GOOGLE LLC 401(K) SAVINGS PLAN', 18576.337,
                                  share_price=18.36)]
        test_account.options = [holding.fund for holding in test_account.holdings]
        mock_account.return_value = test_account
        with mock.patch('portfolio.open', mock.mock_open(read_data=self._account_desc)) as m:
            actual_portfolio = portfolio.build_portfolio('data/accounts.json')

        expected_portfolio = portfolio.Portfolio([test_account])
        self.assertEqual(actual_portfolio, expected_portfolio)


class PortfolioTest(unittest.TestCase):

    def setUp(self):
        fidelity_account = mock.MagicMock(account.Account, autospect=True)
        fidelity_account.name = 'ACME 401(K) SAVINGS PLAN'
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
        self._portfolio = portfolio.Portfolio([fidelity_account, vanguard_account])

    def test_get_allocation_by_asset_class(self):
        allocation_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP,
                                     investment.AssetClass.CASH, investment.AssetClass.REAL_ESTATE], name='asset_class')
        expected_allocation_df = pd.DataFrame(data=[10000.0, 5000.0, 5000.0, 20000.0], index=allocation_index,
                                              columns=['value'])
        expected_allocation_df.sort_index(inplace=True)
        pd.testing.assert_frame_equal(self._portfolio.get_allocation_by_asset_class().sort_index(inplace=False),
                                      expected_allocation_df)

    def test_get_allocation_by_institution(self):
        allocation_index = pd.Index(['Fidelity', 'Vanguard'], name='institution')
        expected_allocation_df = pd.DataFrame(data=[20000.0, 20000.0], index=allocation_index, columns=['value'])
        pd.testing.assert_frame_equal(self._portfolio.get_allocation_by_institution().sort_index(inplace=False),
                                      expected_allocation_df.sort_index(inplace=False))

    def test_get_difference_from_target(self):
        mock_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP,
                               investment.AssetClass.REAL_ESTATE], name='asset_class')
        mock_target = mock.MagicMock(allocation.Target, autospec=True)
        mock_target.dataframe = pd.DataFrame(data=[25.0, 25.0, 50.0], index=mock_index)
        mock_target.num_assets = len(mock_index)
        expected_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP,
                                   investment.AssetClass.REAL_ESTATE, investment.AssetClass.CASH], name='asset_class')
        expected_result = pd.Series(data=[0.000, 12.5, 0.000, -12.5], index=expected_index,
                                    dtype=float)
        pd.testing.assert_series_equal(self._portfolio.get_difference_from_target(mock_target), expected_result)
        pass

    def test_get_percentage_allocation(self):
        allocation_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP,
                                     investment.AssetClass.CASH, investment.AssetClass.REAL_ESTATE],
                                    name='asset_class')
        expected_allocation_df = pd.DataFrame(data={'value': [10000.0, 5000.0, 5000.0, 20000.0],
                                                    'fraction': [0.25, 0.125, 0.125, 0.5],
                                                    'percentage': [25.0, 12.5, 12.5, 50.0]},
                                              index=allocation_index)
        pd.testing.assert_frame_equal(self._portfolio.get_percentage_allocation().sort_index(inplace=False),
                                      expected_allocation_df.sort_index(inplace=False))

    def test_allocate_cash(self):
        mock_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP, \
                               investment.AssetClass.REAL_ESTATE], name='asset_class')
        mock_target = mock.MagicMock(allocation.Target, autospec=True)
        mock_target.dataframe = pd.DataFrame(data=[25.0, 25.0, 50.0], index=mock_index)
        mock_target.num_assets = len(mock_index)
        transactions = self._portfolio.allocate_cash(mock_target)
        expected_transactions = [portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                       'Small Cap Value Fund Class Institutional', 500),
                                 portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                       'Money Market', -5000)
                                 ]
        self.assertCountEqual(transactions, expected_transactions)

    def test_tune_noop(self):
        mock_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP, \
                               investment.AssetClass.REAL_ESTATE], name='asset_class')
        mock_target = mock.MagicMock(allocation.Target, autospec=True)
        mock_target.dataframe = pd.DataFrame(data=[25.0, 25.0, 50.0], index=mock_index)
        mock_target.num_assets = len(mock_index)
        transactions = self._portfolio.tune(mock_target)
        expected_transactions = [portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                       'Small Cap Value Fund Class Institutional', 500),
                                 portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                       'Money Market', -5000)
                                 ]
        self.assertCountEqual(transactions, expected_transactions)

    def test_tune(self):
        vanguard_account = mock.MagicMock(account.Account, autospec=True)
        vanguard_account.name = 'INDIVIDUAL IRA'
        vanguard_account.institution = 'Vanguard'
        vanguard_account.account_file = 'Vanguard_Positions.csv'
        vanguard_account.is_taxable = False
        vanguard_account.holdings = [
            investment.Investment('CRISX', investment.AssetClass.SMALL_CAP, 'Small Cap Value Fund Class Institutional',
                                  3000, share_price=10),
            investment.Investment('FSKAX', investment.AssetClass.CORE_US, 'Fidelity Total Market Index', 2000,
                                  share_price=10),
            investment.Investment('VNQ', investment.AssetClass.REAL_ESTATE, 'Vanguard Real Estate Index Fund', 3000,
                                  share_price=10)
        ]
        vanguard_account.options = [holding.fund for holding in vanguard_account.holdings]
        self._portfolio = portfolio.Portfolio([vanguard_account])
        mock_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP,
                               investment.AssetClass.REAL_ESTATE], name='asset_class')
        mock_target = mock.MagicMock(allocation.Target, autospec=True)
        mock_target.dataframe = pd.DataFrame(data=[25.0, 25.0, 50.0], index=mock_index)
        mock_target.num_assets = len(mock_index)
        transactions = self._portfolio.tune(mock_target)
        expected_transactions = [portfolio.Transaction('Vanguard', 'INDIVIDUAL IRA',
                                                       'Small Cap Value Fund Class Institutional', -1000),
                                 portfolio.Transaction('Vanguard', 'INDIVIDUAL IRA',
                                                       'Vanguard Real Estate Index Fund', 1000)
                                 ]
        self.assertCountEqual(transactions, expected_transactions)

    def test_execute_inplace(self):
        test_transactions = [portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                   'Small Cap Value Fund Class Institutional', 500),
                             portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                   'Money Market', -5000)
                             ]
        self._portfolio.execute(test_transactions, inplace=True)
        allocation_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP,
                                     investment.AssetClass.CASH, investment.AssetClass.REAL_ESTATE],
                                    name='asset_class')
        expected_allocation_df = pd.DataFrame(data={'value': [10000.0, 10000.0, 0.0, 20000.0],
                                                    'fraction': [0.25, 0.25, 0.0, 0.5],
                                                    'percentage': [25.0, 25.0, 0.0, 50.0]},
                                              index=allocation_index)
        pd.testing.assert_frame_equal(self._portfolio.get_percentage_allocation().sort_index(inplace=False),
                                      expected_allocation_df.sort_index(inplace=False))

    def test_execute_not_inplace(self):
        test_transactions = [portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                   'Small Cap Value Fund Class Institutional', 500),
                             portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                   'Money Market', -5000)
                             ]
        test_portolio = self._portfolio.execute(test_transactions, inplace=False)
        allocation_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP,
                                     investment.AssetClass.CASH, investment.AssetClass.REAL_ESTATE],
                                    name='asset_class')
        expected_allocation_df = pd.DataFrame(data={'value': [10000.0, 10000.0, 0.0, 20000.0],
                                                    'fraction': [0.25, 0.25, 0.0, 0.5],
                                                    'percentage': [25.0, 25.0, 0.0, 50.0]},
                                              index=allocation_index)
        pd.testing.assert_frame_equal(test_portolio.get_percentage_allocation().sort_index(inplace=False),
                                      expected_allocation_df.sort_index(inplace=False))

    def test_execute_not_inplace_nochange(self):
        test_transactions = [portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                   'Small Cap Value Fund Class Institutional', 500),
                             portfolio.Transaction('Fidelity', 'ACME 401(K) SAVINGS PLAN',
                                                   'Money Market', -5000)
                             ]
        _ = self._portfolio.execute(test_transactions, inplace=False)
        allocation_index = pd.Index([investment.AssetClass.CORE_US, investment.AssetClass.SMALL_CAP,
                                     investment.AssetClass.CASH, investment.AssetClass.REAL_ESTATE],
                                    name='asset_class')
        expected_allocation_df = pd.DataFrame(data={'value': [10000.0, 5000.0, 5000.0, 20000.0],
                                                    'fraction': [0.25, 0.125, 0.125, 0.5],
                                                    'percentage': [25.0, 12.5, 12.5, 50.0]},
                                              index=allocation_index)
        pd.testing.assert_frame_equal(self._portfolio.get_percentage_allocation().sort_index(inplace=False),
                                      expected_allocation_df.sort_index(inplace=False))



if __name__ == '__main__':
    unittest.main()
