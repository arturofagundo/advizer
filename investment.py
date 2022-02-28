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

"""Defines investment as an abstraction"""
import enum
import functools
from dataclasses import dataclass
import math
from typing import Text, Dict


@enum.unique
@functools.total_ordering
class AssetClass(enum.Enum):
    MONEY_MARKET = enum.auto()
    INVESTMENT_GRADE_BONDS = enum.auto()
    HIGH_YIELD_BONDS = enum.auto()
    INFLATION_PROTECTED_BONDS = enum.auto()
    CORE_US = enum.auto()
    SMALL_CAP = enum.auto()
    MICRO_CAP = enum.auto()
    REAL_ESTATE = enum.auto()
    PACIFIC_RIM_LARGE = enum.auto()
    EUROPE_LARGE = enum.auto()
    INTERNATIONAL_SMALL_CAP_VALUE = enum.auto()
    EMERGING_MARKETS = enum.auto()
    CASH = enum.auto()

    _fixed_income = (INVESTMENT_GRADE_BONDS, HIGH_YIELD_BONDS, INFLATION_PROTECTED_BONDS)

    @property
    def is_fixed_income(self) -> bool:
        """Returns a boolean value indicating if the class is a fixed-income investment."""
        return self in self._fixed_income

    def __str__(self):
        return self.name

    def __lt__(self, other: 'AssetClass'):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented


@dataclass(frozen=True)
class Fund:
    ticker_symbol: Text
    asset_class: AssetClass
    name: Text
    share_price: float

    def __str__(self):
        return self.name


LOOKUP: Dict[str, AssetClass] = dict(VFFSX=AssetClass.CORE_US,
                                     VEXRX=AssetClass.SMALL_CAP,
                                     SCZ=AssetClass.MICRO_CAP,
                                     FSKAX=AssetClass.CORE_US,
                                     IEUR=AssetClass.EUROPE_LARGE,
                                     IPAC=AssetClass.PACIFIC_RIM_LARGE,
                                     x0338=AssetClass.INVESTMENT_GRADE_BONDS,
                                     VBTIX=AssetClass.INVESTMENT_GRADE_BONDS,
                                     CRISX=AssetClass.SMALL_CAP,
                                     VNQ=AssetClass.REAL_ESTATE,
                                     VWO=AssetClass.EMERGING_MARKETS,
                                     CASH=AssetClass.CASH)


class Investment:

    def __init__(self, ticker_symbol: Text, asset_class: AssetClass, name: Text,
                 num_shares: int = 0, share_price: float = None):
        self._fund = Fund(ticker_symbol, asset_class, name, share_price)
        self._ticker_symbol = ticker_symbol
        self._num_shares = num_shares
        self._share_price = share_price

    def __eq__(self, other: 'Investment'):
        return (self._fund == other._fund and self._ticker_symbol == other._ticker_symbol and
                math.isclose(self._num_shares, other._num_shares) and self._share_price == other._share_price)

    @property
    def fund(self):
        return self._fund

    @property
    def ticker_symbol(self):
        return self._ticker_symbol

    @property
    def asset_class(self):
        return self._fund.asset_class

    @property
    def num_shares(self):
        return self._num_shares

    @num_shares.setter
    def num_shares(self, num_shares: int):
        self._num_shares = num_shares

    @property
    def share_price(self):
        return self._share_price

    @property
    def value(self):
        return self._num_shares * self.share_price

    def __str__(self):
        return self._fund + ' holding ' + self._num_shares
