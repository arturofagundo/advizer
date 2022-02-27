# Advizer

## Overview
Perform rudimentary operations on a portfolio of investments across collection of tax advantaged and non-tax advantaged
accounts. For passive investors this library provides a consolidated view of asset allocation across accounts and 
provides guidance on how to allocate cash to more closely align with a target asset allocation.

## Components
* investment - Abstraction for a fund (i.e, either a mutual fund or ETF)
* account - Abstraction for account data. Includes a collection of investments.
* allocation - Essentially a target asset allocation
* portfolio - Abstraction for a collection of accounts

## Workflows
1. Build a portfolio using JSON formatted account description.
2. Optionally build a target portfolio using a JSON formatted target asset allocation.

### Cash Allocation
The call to `allocate_cash` returns a series of `Transaction` objects. These transactions can be executed on 
the portfolio, either `inplace` or on a copy of the portfolio.

### Rebalance AND allocate cash
The call to `tune`, rebalances tax-advantaged accounts and allocates cash within taxable accounts to minimize deviation 
from the specified target allocation. 

The call to `allocate_cash` returns a series of `Transaction` objects. These transactions can be executed on 
the portfolio, either `inplace` or on a copy of the portfolio.

## Future Work
* Make fund descriptions configurable - The mapping from investment to asset class is hard coded in the investment
    module. This should really be read from a json formatted file.
* Model Growth - Estimate distributon of future balance=