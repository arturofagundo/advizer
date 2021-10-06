"""Represents a collection of holdings segregated by account"""
import collections
import copy
import dataclasses
import framing
import functools
import json
import math
from typing import List, Text

import numpy as np
import pandas as pd
from absl import logging
from scipy import optimize

import account
import allocation


def _get_percentage_allocation(current_df: pd.DataFrame) -> pd.DataFrame:
    """
    Gets the percentage allocation by asset class
    :param target:
    :return:
    """
    current_allocation = current_df.groupby(['asset_class'])['value'].agg('sum').to_frame()
    net_value = current_allocation.value.sum()
    current_allocation['fraction'] = current_allocation['value'] / net_value
    current_allocation['percentage'] = current_allocation['fraction'] * 100
    return current_allocation


def _get_diff_from_target(current_df: pd.DataFrame,
                          target: allocation.Target) -> pd.Series:
    """
    Gets the absolute difference in percentage allocation from the target.
    :param target:
    :return:
    """
    current_allocation = _get_percentage_allocation(current_df)
    target_df: pd.DataFrame = target.dataframe
    difference_series = target_df[0].sub(current_allocation['percentage'].astype(float), fill_value=0)
    difference_series.index.name = 'asset_class'
    return difference_series


def _objective_fn(initial: pd.DataFrame, target: pd.DataFrame, x: List[int]) -> float:
    """
    Objective function for use in calculation of the optimal cash allocation
    """
    results = initial.copy()
    results['num_shares'] = results['num_shares'].astype(float) + x
    results['value'] = results['num_shares'].astype(float) * results['share_price'].astype(float)
    logging.debug('_objective_fn(%s)', x)
    logging.debug('_objective_fn: result %f', _get_rmse(results, target))
    return _get_rmse(results, target)


def _get_rmse(current_df: pd.DataFrame, target: pd.DataFrame) -> float:
    """Calculates root mean squared error between target and actual allocation.

    Args:
        target: Target allocation by asset class and percentage allocation
        actual: Actual allocation by asset class and percentage allocation

    Returns:
        Root Mean Square error
    """
    difference_series = _get_diff_from_target(current_df, target)
    square_error = difference_series ** 2
    result: float = square_error.sum() / len(square_error.index)
    return math.sqrt(result)


def build_portfolio(filename: Text) -> 'Portfolio':
    accounts = []
    with open(filename, mode='r', encoding='utf8') as accounts_file:
        account_num = 0
        account_descs = json.load(accounts_file)
        for account_desc in account_descs:
            account_num += 1
            logging.info('Account Number %d,contents: %s', account_num, account_desc)
            accounts.append(account.Account(account_desc))
        logging.info('Processed %d data', account_num)
    return Portfolio(accounts)


@dataclasses.dataclass(frozen=True)
class Transaction:
    institution: Text
    account_name: Text
    fund_name: Text
    num_shares: int

    def __str__(self):
        operation = 'Purchase' if self.num_shares > 0 else 'Sell'
        return f"{operation} {self.num_shares} shares of {self.fund_name} within {self.account_name} at {self.institution}"


class ResultError(Exception):
    pass


class Portfolio:

    def __init__(self, accounts: List[account.Account]):
        self._accounts = accounts
        self._build_dataframe()

    def _build_dataframe(self):
        # Build pd.DataFrame from the data
        columns = ['account_name', 'institution', 'fund_name', 'asset_class', 'ticker_symbol', 'share_price',
                   'num_shares', 'value']
        self._df = pd.DataFrame(columns=columns)
        num_holdings: int = 0
        for acc in self._accounts:
            for holding in acc.holdings:
                fund = holding.fund
                self._df.loc[num_holdings] = [
                    acc.name, acc.institution, fund.name, fund.asset_class, fund.ticker_symbol,
                    float(fund.share_price), float(holding.num_shares), float(holding.value)
                ]
                num_holdings += 1
        self._num_holdings = num_holdings
        self._allocation = self._df.groupby(['asset_class'])['value'].agg('sum').to_frame()
        self._net_value = self._df.value.sum()

    def __str__(self):
        return self._df.to_string()

    def __eq__(self, other: 'Portfolio'):
        return self._df.equals(other._df)

    def _get_linear_constraint(self) -> 'optimize.LinearConstraint':
        account_number = 0
        curr_account = self._df.iloc[0]['account_name']
        coefficients = [[0]*self._num_holdings]
        coefficients[account_number][0] = self._df.iloc[0]['share_price']
        num_accounts = len(self._df['account_name'].unique())
        bound = [0] * num_accounts
        for row_number in self._df.index[1:]:
            new_account = self._df.iloc[row_number]['account_name']
            if new_account != curr_account:
                curr_account = new_account
                account_number += 1
                coefficients.append([0] * self._num_holdings)
            coefficients[account_number][row_number] = self._df.iloc[row_number]['share_price']
        return optimize.LinearConstraint(np.array(coefficients), bound, bound)

    def get_allocation_by_asset_class(self) -> pd.DataFrame:
        """
        Gets the allocations by asset class in this portfolio

        :return: pd.DataFrame
        """
        return self._df.groupby(['asset_class'])['value'].agg('sum').to_frame()

    def get_allocation_by_institution(self) -> pd.DataFrame:
        """
        Gets the allocations by asset class in this portfolio

        :return: pd.DataFrame
        """
        return self._df.groupby(['institution'])['value'].agg('sum').to_frame()

    def get_difference_from_target(self, target: pd.DataFrame) -> pd.Series:
        """
        Gets the difference in asset allocation from the target asset allocation.
        :param target:
        :return:
        """
        return _get_diff_from_target(self._df, target)

    def get_percentage_allocation(self) -> pd.DataFrame:
        """
        Gets the percentage allocation by asset class.
        :param self:
        :return:
        """
        return _get_percentage_allocation(self._df)

    def allocate_cash(self, target: pd.DataFrame) -> pd.DataFrame:
        """
        Gets the optimal cash ollocation for the portfolio

        Throws:
            ResultError if no optimal cash allocation can be found
        """
        framing_context = framing.Context(taxable=framing.CashAllocationStrategy())
        return self._optimize_allocation(framing_context, target)

    def tune(self, target: pd.DataFrame) -> pd.DataFrame:
        """
        Re-balances tax advantaged data and allooctes cash for taxable data

        Throws:
            ResultError if no optimal cash allocation can be found
        """
        framing_context = framing.Context(taxable=framing.CashAllocationStrategy(),
                                          non_taxable=framing.RebalanceAllocationStrategy())
        return self._optimize_allocation(framing_context, target)

    def _optimize_allocation(self, framing_context, target):
        bnds = framing_context.get_allocation_bounds(self._df, self._accounts)
        x0 = framing_context.get_initial_allocation(self._df, self._accounts)
        logging.info('Initial objective fn value: %f', _objective_fn(self._df, target, x0))
        cons = [self._get_linear_constraint()]
        solution = optimize.minimize(functools.partial(_objective_fn, self._df, target),
                                     x0, method='SLSQP', bounds=bnds, constraints=cons, tol=1e-10)
        if not solution.success:
            raise ResultError(f"Cash allocation failed: {solution.message}")
        result = []
        for holding in range(len(solution.x)):
            logging.info('Cash allocation: %f shares of %s from account %s held at %s', round(solution.x[holding], 2),
                         self._df.iloc[holding]['fund_name'], self._df.iloc[holding]['account_name'],
                         self._df.iloc[holding]['institution'])
            if abs(solution.x[holding]) > 1e-02:
                institution = self._df.iloc[holding]['institution']
                account_name = self._df.iloc[holding]['account_name']
                fund_name = self._df.iloc[holding]['fund_name']
                result.append(Transaction(institution, account_name, fund_name,
                                          round(solution.x[holding], 2)))
        logging.info('Final objective fn value: %f', _objective_fn(self._df, target, solution.x))
        return result

    def execute(self, transactions: List[Transaction], inplace=False) -> 'Portfolio':
        """
        Executes a list of transactions an the current portfolio and optionally returns a copy.
        :rtype: object
        :param transactions: A series of fund puchases/sales
        :param in_place: Make a copy of current portfolio if False
        :return: None or a modified copy of the current portfolio if in_place is set to False
        """
        transact_map = collections.defaultdict(lambda: collections.defaultdict(float))
        for transaction in transactions:
            transact_map[transaction.account_name][transaction.fund_name] = transaction.num_shares
        account_list = self._accounts if inplace else copy.deepcopy(self._accounts)
        for accnt in account_list:
            holdings = accnt.holdings
            for holding in holdings:
                holding.num_shares = holding.num_shares + transact_map[accnt.name][holding.fund.name]
            accnt.holdings = holdings

        if inplace:
            self._build_dataframe()
            return self
        else:
            return Portfolio(account_list)





