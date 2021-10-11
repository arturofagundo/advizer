# DISCLAIMER: This is not an officially supported Google product

# Advizer

## Overview
Perform rudimentary operations on a portfolio of investments across collection of tax advantaged and non-tax advantaged
accounts. For passive investors this library provides a consolidated view of asset allocation across accounts and 
provides guidance on how to allocate cash to more closely align with a target asset allocation.

## Usage Instructions
1. Download your account data to data/user.
2. Add an accounts.json file which describes the account summary name(s) along with a with a JSON formatted schema
definition: Essentially specify the column headers used in your csv file to specify the following fields:

 * share_price: The per share price in dollars of the assest in a given row at
   the time that the asset summary was downloaded
 * num_shares:  The number of shares currently held
 * description: The textual description of the investment
 * symbol:      The ticker symbol for the investment. This is used to lookup the
   asset class for the investment and can be problematic as Vanguard does not
   provide a ticker symbol. In such cases, for now the symbol must simply be
   added manually. See open issues below for more information.

3. Optionally setup a virtual env environment to run the advize tool
4. Install the requirements identifieed in requirements.txt.

```pip install -r requirements.txt```

5. Run the tool, specifying a '--account_dir' flag as follows:
```python advize.py --account_dir=data/user```


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

## Open Issues
* Simplify asset class to investment matching
* Pass the account_dir path to the account.Account initializer call: Currently
  this code looks under the 'data' directory and that is hardcoded.
* Add a --verbose flag to enable debug logging when necessary
* Add a summary view which highlights profile comparison to target asset
  allocation
* Improve search for optimal re-balancing by attempting allocation optimization
  over a range of initial values
* Provide distinct command for allocation of cash and tuning of the overall
  portfolio

## Future Work
* Make fund descriptions configurable - The mapping from investment to asset class is hard coded in the investment
    module. This should really be read from a json formatted file.
* Model Growth - Estimate distributon of future balance=
