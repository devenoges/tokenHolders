#!/usr/bin/env python3
#
# Copyright (C) 2018 devenoges
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Get Ethereum ERC20 Transfer Event Logs with Infura

Example invocation:
    INFURA_API_KEY=<Your-Infura-Key> python3 tokenHolders.py -d 18 -t ERC20-Contract-Address > transfers.json
"""

import argparse, os, sys
from collections import defaultdict
from decimal import Decimal

import requests
import simplejson as json

INFURA_KEY = os.environ.get("INFURA_KEY")

ERC20_TRANSFER_EVENT_TOPIC_HASH = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def callInfura(method: str, params: dict) -> dict:
    data = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1}
    response = requests.post(f'https://mainnet.infura.io/{INFURA_KEY}', headers={'Content-Type': 'application/json'}, json=data)
    print(f'Got infura response {response}', file=sys.stderr)
    return response.json()

def getTransferEventLogs(address: str, decimals: int, fromBlock='earliest', toBlock='latest') -> list:
    logs = callInfura('eth_getLogs',
            [{'address': address, 'fromBlock': fromBlock, 'toBlock': toBlock, 'topics': [ERC20_TRANSFER_EVENT_TOPIC_HASH]}])['result']
    decimalFactor = Decimal('10') ** Decimal(f'-{decimals}')
    print(f'Processing {len(logs)} transfer events', file=sys.stderr)
    for log in logs:
        log['from'] = '0x' + log['topics'][1][26:]
        log['to'] = '0x' + log['topics'][2][26:]
        log['amount'] = Decimal(str(int(log['data'], 16))) * decimalFactor
    return logs

def getBalances(transfers: list, toBlock=None, cutoff=None) -> list:
    """
    Assumes transfers are sorted by blockNumber.
    toBlock: int
    cutoff: Decimal
    """
    balances = defaultdict(Decimal)
    for t in transfers:
        if toBlock is not None and int(t['blockNumber'], 16) > toBlock:
            break
        balances[t['from']] -= t['amount']
        balances[t['to']] += t['amount']

    balances = {k: v for k, v in balances.items() if v > Decimal('0')}

    if cutoff is None:
        balances = [{'address': k, 'amount': v} for k, v in balances.items()]
    else:
        balances = [{'address': k, 'amount': v} for k, v in balances.items() if v >= cutoff]

    balances = sorted(balances, key=lambda x: -abs(x['amount']))
    return balances

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='tokenHolders.py', formatter_class=argparse.RawTextHelpFormatter,
            description='Requires the environment variable INFURA_API_KEY to be set.',
            epilog='e.g. INFURA_API_KEY=<Your-Infura-Key> ./tokenHolders.py 0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2 > MKR_bal.json')
    parser.add_argument('contract', help='ERC20 contract address', type=str)
    parser.add_argument('-d', '--decimals', help='ERC20 contract decimals (default 18)', default=18, type=int)
    parser.add_argument('-t', '--transfers', help='Print transfer events (default print address balances)', default=False, action='store_true')
    arguments = parser.parse_args()

    tx = getTransferEventLogs(arguments.contract, arguments.decimals)
    if arguments.transfers:
        print(json.dumps(tx, indent=4))
    else:
        balances = getBalances(tx)
        print(json.dumps(balances, indent=4))
