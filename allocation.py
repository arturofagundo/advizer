"""Defines asset allocation as an abstraction."""

from absl import logging
import copy
import json
from abc import ABC
from typing import Dict, Text
import pandas as pd

import investment


class Allocation(ABC):
    """Defines a percentage allocation to various asset classes.

    Initialized with a dictionary which matches a textual description of an
    asset class to a percentage allocation.
    """

    def __init__(self, asset_class: Dict[investment.AssetClass, float]):
        self._asset_class = pd.DataFrame.from_dict(asset_class, orient='index')

    @property
    def dataframe(self):
        return copy.copy(self._asset_class)

    @property
    def num_assets(self) -> int:
        return len(self._asset_class.index)

    def __sub__(self, other) -> pd.DataFrame:
        return self._asset_class.sub(other.dataframe, fill_value=0)

    _desc2assetclass: Dict[str, investment.AssetClass] = {
        'Money Market': investment.AssetClass.MONEY_MARKET,
        'Investment Grade Bonds': investment.AssetClass.INVESTMENT_GRADE_BONDS,
        'High Yield Bonds': investment.AssetClass.HIGH_YIELD_BONDS,
        'Inflation Protected Bonds': investment.AssetClass.INFLATION_PROTECTED_BONDS,
        'Core U.S.': investment.AssetClass.CORE_US,
        'Small Cap': investment.AssetClass.SMALL_CAP,
        'Microcap': investment.AssetClass.MICRO_CAP,
        'Real Estate': investment.AssetClass.REAL_ESTATE,
        'Pacific Rim Large': investment.AssetClass.PACIFIC_RIM_LARGE,
        'Europe Large': investment.AssetClass.EUROPE_LARGE,
        'International Small Cap Value': investment.AssetClass.INTERNATIONAL_SMALL_CAP_VALUE,
        'Emerging Markets': investment.AssetClass.EMERGING_MARKETS,
        'Cash': investment.AssetClass.CASH
    }


class Target(Allocation):
    """Represents target investments by dollar percentage investment."""

    def __init__(self, filename: Text):
        self._allocation = {}
        logging.info('Target Allocation Definition: %s', filename)
        with open(filename, mode='r', encoding='utf8') as target:
            asset_classes = json.load(target)
            for asset_class in asset_classes:
                logging.info('Target Allocation: %s', asset_class)
                key = asset_class['asset_class']
                val = asset_class['allocation']
                self._allocation[self._desc2assetclass[key]] = float(val) * 100
        super(Target, self).__init__(self._allocation)

    def __str__(self):
        return_value = 'Target Allocation\n'
        assets = sorted(self._allocation.items(), key=lambda x: x[0].name)
        for asset_class, percentage in assets:
            return_value += f'{asset_class}: {percentage:.2f}%\n'
        return return_value

    @property
    def asset_class(self):
        return self._allocation.keys()