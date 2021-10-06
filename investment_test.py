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

import investment
import unittest


class InvestmentTest(unittest.TestCase):
    def setUp(self):
        self._investment = investment.Investment('msft', investment.AssetClass.CORE_US, 'Microsoft', 5, 40.0)

    def test_equality(self):
        expected_investment = investment.Investment('msft', investment.AssetClass.CORE_US, 'Microsoft', 5, 40.0)
        self.assertEqual(self._investment, expected_investment)

    def test_fund(self):
        expected_fund = investment.Fund('msft', investment.AssetClass.CORE_US, 'Microsoft', 40.0)
        self.assertEqual(expected_fund, self._investment.fund)

    def test_ticker_symbol(self):
        self.assertEqual(self._investment.ticker_symbol, 'msft')

    def test_asset_class(self):
        expected_fund = investment.Fund('msft', investment.AssetClass.CORE_US, 'Microsoft', 40.0)
        self.assertEqual(self._investment.asset_class, expected_fund.asset_class)

    def test_num_shares(self):
        self._investment.num_shares = 10
        self.assertEqual(self._investment.num_shares, 10)

    def test_share_price(self):
        self.assertEqual(self._investment.share_price, 40.0)

    def test_value(self):
        self.assertEqual(self._investment.value, 40.0*5)


if __name__ == '__main__':
    unittest.main()
