import unittest

import allocation
import investment
import mock
import pandas as pd


class TargetAllocationTest(unittest.TestCase):

    def setUp(self):
        self._allocation = [
          {
            "asset_class": "Investment Grade Bonds",
            "allocation": ".2"
          },
          {
            "asset_class": "Core U.S.",
            "allocation": ".3"
          },
          {
            "asset_class": "Small Cap",
            "allocation": ".2"
          },
          {
            "asset_class": "Pacific Rim Large",
            "allocation": ".3"
          },
          {
            "asset_class": "Cash",
            "allocation": ".0"
          }
        ]

        self._allocation_data = """
        [
          {
            "asset_class": "Investment Grade Bonds",
            "allocation": ".2"
          },
          {
            "asset_class": "Core U.S.",
            "allocation": ".3"
          },
          {
            "asset_class": "Small Cap",
            "allocation": ".2"
          },
          {
            "asset_class": "Pacific Rim Large",
            "allocation": ".3"
          },
          {
            "asset_class": "Cash",
            "allocation": ".0"
          }
        ]
        """
        with mock.patch('allocation.open', mock.mock_open(read_data=self._allocation_data)) as m:
            self._allocation = allocation.Target('data/target.json')

    def test_as_dataframe(self):
        expected = {investment.AssetClass.INVESTMENT_GRADE_BONDS: float(20),
                    investment.AssetClass.CORE_US: float(30),
                    investment.AssetClass.SMALL_CAP: float(20),
                    investment.AssetClass.PACIFIC_RIM_LARGE: float(30),
                    investment.AssetClass.CASH: float(0)
                    }
        expected_pd = pd.DataFrame.from_dict(expected, orient='index')
        pd.testing.assert_frame_equal(self._allocation.dataframe, expected_pd)


if __name__ == '__main__':
    unittest.main()
