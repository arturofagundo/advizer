import unittest
import account
import decimal
import investment
import mock


class AccountTest(unittest.TestCase):

    def setUp(self):
        self._account_desc = {
            'institution': 'Fidelity',
            'name': 'Joint WROS',
            'filename': 'Personal_Account_Positions.csv',
            'taxable': 'True',
            'headers': {
                'name': 'Account Name/Number',
                'symbol': 'Symbol',
                'description': 'Description',
                'num_shares': 'Quantity',
                'share_price': 'Last Price'
            }
        }
        self._account_data = ('Account Name/Number,Symbol,Description,Quantity,Last Price,Last Price Change,'
                              'Current Value,Today\'s Gain/Loss Dollar,Today\'s Gain/Loss Percent,'
                              'Total Gain/Loss Dollar,Total Gain/Loss Percent,Percent Of Account,Cost Basis,'
                              'Cost Basis Per Share,Type\n'
                              'X31448117,FSKAX,FIDELITY TOTAL MARKET INDEX FUND,"2,337.151",$110.25,+$0.52,'
                              '"$257,670.89","+$1,215.31",+0.47%,"+$50,378.54",+24.30%,46.96%,"$207,292.35",'
                              '$88.69,Cash,\n')
        with mock.patch('account.open', mock.mock_open(read_data=self._account_data)) as m:
            self._account = account.Account(self._account_desc)

    def test_holdings(self):
        expected_holdings = [investment.Investment('FSKAX', investment.AssetClass.CORE_US,
                                                   'FIDELITY TOTAL MARKET INDEX FUND',
                                                   decimal.Decimal(2337.151), share_price=110.25)]
        self.assertCountEqual(self._account.holdings, expected_holdings)

    def test_investment_options(self):
        expected_funds = [investment.Fund('FSKAX', investment.AssetClass.CORE_US, 'FIDELITY TOTAL MARKET INDEX FUND',
                                          110.25)]
        self.assertCountEqual(self._account.investment_options, expected_funds)

    def test_is_taxable(self):
        self.assertTrue(self._account.is_taxable, True)

    def test_cash(self):
        self.assertAlmostEqual(self._account.cash, 0.0)


if __name__ == '__main__':
    unittest.main()
