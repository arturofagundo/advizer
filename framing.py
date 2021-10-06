"""Defines initial allocation strategy pattern."""

from typing import Any, List, Tuple
import abc
import account
import investment
import numpy as np
import pandas as pd

_JITTER = 1e-10


def combine(x0_taxable: List[Any], x0_non_taxable: List[Any],
            df: pd.DataFrame, taxable: List[str]) -> List[Any]:
    """
    Combines the results of taxable and non-taxable parameter construction.

    :param x0_taxable: List of taxable framing parameter values
    :param x0_non_taxable: List of non-taxable framing parameter values
    :param df: Underlying portfolio data as a Pandas dataframe
    :param taxable: List of taxable account names
    :return: List of combined framing values
    """
    x0 = [0.] * len(df.index)
    for holding in range(len(df.index)):
        if df.loc[holding].account_name in taxable:
            x0[holding] = x0_taxable[holding]
        else:
            x0[holding] = x0_non_taxable[holding]
    return x0


class Context:
    """
    Defines the interface to be used to seed the allocation engine
    """

    def __init__(self, taxable: 'Strategy' = None, non_taxable: 'Strategy' = None) -> None:
        self._taxable = taxable
        self._non_taxable = non_taxable

    @property
    def taxable(self) -> 'Strategy':
        return self._taxable

    @taxable.setter
    def taxable(self, strategy: 'Strategy') -> None:
        self._taxable = strategy

    @property
    def non_taxable(self) -> 'Strategy':
        return self._non_taxable

    @non_taxable.setter
    def non_taxable(self, strategy: 'Strategy') -> None:
        self._non_taxable = strategy

    def get_initial_allocation(self, df: pd.DataFrame,
                               accounts: List[account.Account]) -> np.ndarray:
        """
        Executes the concrete strategy and returns the array of initial holding values
        :rtype: object
        :return:
        """
        taxable = [acct.name for acct in accounts if acct.is_taxable]
        non_taxable = [acct.name for acct in accounts if not acct.is_taxable]
        x0_taxable = x0_non_taxable = np.zeros(len(df.index))
        if self._taxable is not None and len(taxable) > 0:
            x0_taxable = self._taxable.initial_allocation(df, taxable)
        if self._non_taxable is not None and len(non_taxable) > 0:
            x0_non_taxable = self._non_taxable.initial_allocation(df, non_taxable)
        return np.asarray(combine(x0_taxable, x0_non_taxable, df, taxable))

    def get_allocation_bounds(self, df: pd.DataFrame,
                              accounts: List[account.Account]) -> List[Tuple[float, float]]:
        """
        Executes the concrete strategy and returns the array of initial holding values
        :return:
        """
        taxable = [acct.name for acct in accounts if acct.is_taxable]
        non_taxable = [acct.name for acct in accounts if not acct.is_taxable]
        bounds_taxable = bounds_non_taxable = [(0, _JITTER)] * len(df.index)
        if self._taxable is not None and len(taxable) > 0:
            bounds_taxable = self._taxable.bounds(df, taxable)
        if self._non_taxable is not None and len(non_taxable) > 0:
            bounds_non_taxable = self._non_taxable.bounds(df, non_taxable)
        return combine(bounds_taxable, bounds_non_taxable, df, taxable)


class Strategy(abc.ABC):
    """
    The Strategy interface declares operations common to all supported versions
    of some algorithm.

    The SeedingContext uses this interface to call the algorithm defined by Concrete
    Strategies.
    """

    @abc.abstractmethod
    def initial_allocation(self, df: pd.DataFrame, accounts: List[str]) -> np.ndarray:
        raise NotImplemented()

    @abc.abstractmethod
    def bounds(self, df: pd.DataFrame, accounts: List[str]) -> List[Tuple[float, float]]:
        raise NotImplemented()


def _get_cash(df: pd.DataFrame, account_name: str) -> float:
    cash_holdings = df.loc[(df['account_name'] == account_name) &
                           (df['asset_class'] == investment.AssetClass.CASH)]
    return cash_holdings.value.agg('sum')


class CashAllocationStrategy(Strategy):
    """Applied to cash, typically in taxable data. """

    def initial_allocation(self, df: pd.DataFrame, accounts: List[str]) -> np.ndarray:
        """
        Gets an initial allocation of all cash into the existing funds held within each account.

        This strategy ensures that all cash is allocated to non-cash holdings by recommending the purchase of shares
        equivalent to the cash available to the largest current holding.

        :param: df: Underlying portfolio in Pandas DataFrame format
        :param: data: List of account names to operate on
        :return: Number of shares of all holdings in the portfolio to use as an initial starting point
        """
        num_holdings = len(df.index)
        x0 = np.zeros(num_holdings)
        for acct in accounts:
            total_cash = _get_cash(df, acct)
            if total_cash > 0:
                non_cash_holdings = df.loc[(df['account_name'] == acct) &
                                           (df['asset_class'] != investment.AssetClass.CASH)]
                max_idx = non_cash_holdings.value.idxmax()
                x0[max_idx] = total_cash / df.iloc[max_idx].share_price
                cash_holdings = df.loc[(df['account_name'] == acct) &
                                       (df['asset_class'] == investment.AssetClass.CASH)]
                for holding in cash_holdings.index:
                    x0[holding] = -df.iloc[holding].value
        return x0

    def bounds(self, df: pd.DataFrame, accounts: List[str]) -> List[Tuple[float, float]]:
        """
        Gets the cash bounded purchase limits for each holding within the portfolio.

        This should be (0, the Cash Position for the account / share price)
        For the cash holding the bound are (-Cash position, -Cash position + jitter)

        Due to an issue in scipy.optimize.minimize (see https://github.com/scipy/scipy/issues/12502)
        the upper and lower bounds cannot be equal. Adding a small difference to the upper bound
        gets past this problem.

        :param: df: Underlying portfolio in Pandas DataFrame format
        :param: data: List of account names for which we need bounds
        :return: List of bounds
        """
        num_holdings = len(df.index)
        bounds = [(0, 0)] * num_holdings
        for acct in accounts:
            holdings = df.loc[(df['account_name'] == acct)]
            for holding in holdings.index:
                if df.iloc[holding]['asset_class'] == investment.AssetClass.CASH:
                    bounds[holding] = (-df.iloc[holding]['value'],
                                       _JITTER - df.iloc[holding]['value'])
                    continue
                cash = _get_cash(df, acct)
                share_price = df.iloc[holding]['share_price']
                upper_bound = cash / share_price
                bounds[holding] = (0, upper_bound)

        return bounds


class RebalanceAllocationStrategy(Strategy):
    """Applied to re-balancing assets within an account, typically non-taxable data."""

    def initial_allocation(self, df: pd.DataFrame, _: List[str]) -> np.ndarray:
        """
        Gets an initial allocation of funds within an account to specific holdings.

        This strategy uses the current allocation as the initial allocation.

        :param: df: Underlying portfolio in Pandas DataFrame format
        :return: Number of shares of all holdings in the portfolio to use as an initial starting point
        """
        num_holdings = len(df.index)
        return np.zeros(num_holdings)

    def bounds(self, df: pd.DataFrame, accounts: List[str]) -> List[Tuple[float, float]]:
        """
        Gets the bounds on a per holding basis for the potential calculated transactions.

        For non-taxable data, the lower bound is the total number of shares and the upper bound
        is the total account value / share price
        :param: df: Portfolio in a Pandas DataFrame format
        :return: Bounds on a per holding basis.
        """
        num_holdings = len(df.index)
        bounds = [(0, _JITTER)] * num_holdings
        for acct in accounts:
            holdings = df.loc[(df.account_name == acct)]
            account_value = holdings.value.agg('sum')
            if len(holdings.index) <= 1:
                continue
            for holding in holdings.index:
                available = account_value - df.loc[holding].value
                bounds[holding] = (-df.iloc[holding].num_shares,
                                   available / df.loc[holding].share_price)
        return bounds
