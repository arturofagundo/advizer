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

"""Investment account abstraction"""
from absl import logging
import copy
import csv
import os
from typing import Dict, List, Text, Union
import re

import investment

ACCOUNT_SUBDIR = "data"


class Account:
    """An abstraction layer for various types of investment data."""

    def __init__(self, account_desc: Dict[Text, Union[Text, Dict[Text, Text]]]):
        self._name = account_desc['name']
        self._institution = account_desc['institution']
        self._account_file = account_desc['filename']
        self._is_taxable = True if account_desc['taxable'] == 'True' else False
        self._holdings = []
        self._get_holdings(account_desc)
        self._options = [holding.fund for holding in self._holdings]

    def _get_holdings(self, account_desc: Dict[Text, Union[Text, Dict[Text, Text]]]
                      ) -> List[investment.Investment]:
        account_file: str = os.path.join(ACCOUNT_SUBDIR, account_desc['filename'])
        header_to_type = {val: key for key, val in account_desc['headers'].items()}
        with open(account_file) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',')
            line_count = 0
            col_mapping = {}
            for row in csv_reader:
                if not line_count:
                    column_headers = row
                    for index, ele in enumerate(column_headers):
                        if ele in header_to_type:
                            col_mapping[header_to_type[ele]] = index
                    logging.info('Column names are %s', ', '.join(column_headers))
                    logging.info('%s, : col_mapping %s', __name__, col_mapping)
                    line_count += 1
                else:
                    logging.info('%s, Processing: %s', __name__, row)
                    ticker_symbol = row[col_mapping['symbol']]
                    name = row[col_mapping['description']]
                    if ticker_symbol not in investment.LOOKUP:
                        logging.warning('Missing %s from account %s', ticker_symbol, name)
                        continue
                    asset_class = investment.LOOKUP[ticker_symbol]
                    num_shares = row[col_mapping['num_shares']]
                    num_shares = float(re.sub('[^\d.]', '', num_shares))
                    share_price = row[col_mapping['share_price']]
                    share_price = float(re.sub('[^\d.]', '', share_price))
                    holding = investment.Investment(ticker_symbol, asset_class, name,
                                                    num_shares, share_price=share_price)
                    self._holdings.append(holding)
                    row_str = '\t'.join(row)
                    logging.info(row_str)
                    line_count += 1
            logging.info(f'Processed {line_count} lines.')

    @property
    def name(self):
        return self._name

    @property
    def institution(self):
        return self._institution

    @property
    def holdings(self) -> List[investment.Investment]:
        return copy.deepcopy(self._holdings)

    @holdings.setter
    def holdings(self, holdings: List[investment.Investment]):
        self._holdings = holdings

    @property
    def investment_options(self):
        return copy.deepcopy(self._options)

    @property
    def is_taxable(self):
        return self._is_taxable

    @property
    def cash(self) -> float:
        """Gets the amount of cash in this account.
        """
        cash = 0.0
        for holding in self._holdings:
            if holding.asset_class == investment.AssetClass.CASH:
                cash += holding.value

        return cash

    def __str__(self):
        result = f'{self._name} at {self._institution} with {len(self._holdings)}'
        if len(self._holdings) > 0:
            result += '\n'
            for holding in self._holdings:
                result += f'  {holding.num_shares} of {holding.fund}\n'
        return result

    def __repr__(self):
        result = f'{self._name} at {self._institution} with {len(self._holdings)} holdings'
        if len(self._holdings) > 0:
            result += '\n'
            for holding in self._holdings:
                result += f'  {holding.num_shares} of {holding.fund}\n'
        return result
