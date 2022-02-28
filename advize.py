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

# Calculate investment choices
from absl import app
from absl import flags
from absl import logging
import allocation
import pathlib
import portfolio

FLAGS = flags.FLAGS
flags.DEFINE_string('current', 'accounts.json',
                    'List of files containing current allocation. One file per investment account')
flags.DEFINE_string('target', 'target.json', 'Target Asset Allocation.')
flags.DEFINE_string('account_dir', 'data', 'Directory containing account data and target allocation')
flags.DEFINE_bool('verbose', False, 'Set logging to verbose')


def main(unused_argv):
    if not FLAGS.log_dir:
        FLAGS.log_dir = 'logs'
    print('All logs being dumped to', FLAGS.log_dir)
    logging.get_absl_handler().use_absl_log_file()
    if FLAGS.verbose:
        logging.set_verbosity(logging.DEBUG)
    # Use a breakpoint in the code line below to debug your script.

    target_path = pathlib.Path(FLAGS.account_dir, FLAGS.target)
    target_allocation = allocation.Target(target_path)
    print(target_allocation)
    accounts_path = pathlib.Path(FLAGS.account_dir, FLAGS.current)
    my_portfolio = portfolio.build_portfolio(accounts_path)
    print(my_portfolio)
    pf_by_asset_class = my_portfolio.get_allocation_by_asset_class()
    print(pf_by_asset_class)
    percentage_allocation = my_portfolio.get_percentage_allocation()
    print(percentage_allocation)

    transactions = my_portfolio.allocate_cash(target_allocation)
    print(f'Number of transactions: {len(transactions)}')
    for transaction in transactions:
        print(transaction)

    my_portfolio.execute(transactions)


if __name__ == '__main__':
    app.run(main)
