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

Example invocations:
    INFURA_API_KEY=<Your-Infura-Key> python3 tokenHolders.py -d 18 -t ERC20-Contract-Address > transfers.json

    tokenHolders.py -d 8 -t 0x168296bb09e24a88805cb9c33356536b980d3fc5 > tx.RHOC.0x168296bb09e24a88805cb9c33356536b980d3fc5.json
    tokenHolders.py -d 9 -t 0xe0b7927c4af23765cb51314a0e0521a9645f0e2a > tx.DGD.0xe0b7927c4af23765cb51314a0e0521a9645f0e2a.json
    tokenHolders.py -d 9 -t 0x4f3afec4e5a3f2a6a1a411def7d7dfe50ee057bf > tx.DGX.0x4f3afec4e5a3f2a6a1a411def7d7dfe50ee057bf.json
    tokenHolders.py -t 0xB8c77482e45F1F44dE1745F52C74426C631bDD52  > tx.BNB.0xB8c77482e45F1F44dE1745F52C74426C631bDD52.json

    tokenHolders.py -t 0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359  > tx.DAI.0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359.json

    tokenHolders.py -t 0x8dd5fbce2f6a956c3022ba3663759011dd51e73e  > tx.TUSD.0x8dd5fbce2f6a956c3022ba3663759011dd51e73e.json

    tokenHolders.py -t 0xd26114cd6EE289AccF82350c8d8487fedB8A0C07  > tx.OMG.0xd26114cd6EE289AccF82350c8d8487fedB8A0C07.json


TODO:
    add csv output option
    eg:
Txhash	Blockno	UnixTimestamp	DateTime	From	To	Quantity
0xb38301fecc96ba942229f82578420b85d6882dc7dbdcdf9d9f31ec226283cc95	4832688	1514764814	1/1/2018 12:00:14 AM	0xf73c3c65bde10bf26c2e1763104e609a41702efe	0x26e6fd6597965bed2875f08e8a7545c2389ba69d	13.8845
"""

import argparse, os, sys
from collections import defaultdict
from decimal import Decimal

import requests
import simplejson as json
import numpy as np

INFURA_API_KEY = os.environ['INFURA_API_KEY']

ERC20_TRANSFER_EVENT_TOPIC_HASH = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"

def gini(array, filterZero=False):
    """
    Calculate the Gini coefficient of a numpy array.

    All values are treated equally, arrays must be 1d.

    see:
        http://neuroplausible.com/gini
        https://github.com/oliviaguest/gini (CC0 licence)
    based on bottom eq:
        http://www.statsdirect.com/help/generatedimages/equations/equation154.svg
    from:
        http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    """
    array = array.flatten()
    if np.amin(array) < 0:
        # Values cannot be negative:
        array -= np.amin(array)
    # Values cannot be 0:
    if filterZero:
        array = (array != Decimal('0'))
    # Values must be sorted:
    array = np.sort(array)
    # Index per array element:
    index = np.arange(1, array.shape[0]+1)
    # Number of array elements:
    n = array.shape[0]
    # Gini coefficient:
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

def callInfura(method: str, params: dict) -> dict:
    data = {'jsonrpc': '2.0', 'method': method, 'params': params, 'id': 1}
    response = requests.post(f'https://mainnet.infura.io/{INFURA_API_KEY}', headers={'Content-Type': 'application/json'}, json=data)
    print(f'Infura response {response}', file=sys.stderr)
    response.raise_for_status()
    return response.json()

def getTransferEventLogs(address: str, decimals: int, fromBlock='earliest', toBlock='latest', useChunking=True, chunkSize=50000) -> list:
    """
    TODO:
        check block range step
        write logs as they are receved
        resume partial log download
    """
    if useChunking:
        logs = []
        firstLogBlock = 1
        lastLogBlock = int(callInfura('eth_blockNumber', [{}])['result'], 16)
        print(f'1st: {firstLogBlock} last: {lastLogBlock}', file=sys.stderr)
        logs = []
        for block in range(firstLogBlock, lastLogBlock, chunkSize):
            attempts = 0
            while attempts <= 3:
                try:
                    log = callInfura('eth_getLogs',
                            [{'address': address, 'fromBlock': hex(block), 'toBlock': hex(block + chunkSize), 'topics': [ERC20_TRANSFER_EVENT_TOPIC_HASH]}])['result']
                    logs += log
                    print(f'{len(log)} logs for range {block} to {block + chunkSize}', file=sys.stderr)
                    break
                except requests.exceptions.RequestException as ex:
                    attempts += 1
                    if attempts > 3:
                        raise ex
                    else:
                        print (f'Error getting logs from Infura {ex}, retrying', file=sys.stderr)
    else:
        logs = callInfura('eth_getLogs',
                [{'address': address, 'fromBlock': fromBlock, 'toBlock': toBlock, 'topics': [ERC20_TRANSFER_EVENT_TOPIC_HASH]}])['result']

    decimalFactor = Decimal('10') ** Decimal(f'-{decimals}')
    print(f'Processing {len(logs)} transfer events', file=sys.stderr)
    for log in logs:
        log['from'] = '0x' + log['topics'][1][26:]
        log['to'] = '0x' + log['topics'][2][26:]
        log['amount'] = Decimal(str(int(log['data'], 16))) * decimalFactor
    return logs

def getTransferEventLogsCSV(address: str, decimals: int, fromBlock='earliest', toBlock='latest', chunkSize=50000):
    """
    TODO:
        check block range step
        write logs as they are receved
        resume partial log download
    """
    firstLogBlock = 1
    lastLogBlock = int(callInfura('eth_blockNumber', [{}])['result'], 16)
    print(f'1st: {firstLogBlock} last: {lastLogBlock}', file=sys.stderr)
    decimalFactor = Decimal('10') ** Decimal(f'-{decimals}')
    for block in range(firstLogBlock, lastLogBlock, chunkSize):
        attempts = 0
        while attempts <= 3:
            try:
                logs = callInfura('eth_getLogs',
                        [{'address': address, 'fromBlock': hex(block), 'toBlock': hex(block + chunkSize), 'topics': [ERC20_TRANSFER_EVENT_TOPIC_HASH]}])['result']
                #logs += log
                print(f'Processing {len(logs)} transfer events', file=sys.stderr)
                for log in logs:
                    log['from'] = '0x' + log['topics'][1][26:]
                    log['to'] = '0x' + log['topics'][2][26:]
                    log['amount'] = Decimal(str(int(log['data'], 16))) * decimalFactor
                    #FIXME include datetime and timestamp
                    print(f"{int(log['blockNumber'], 16)},{log['from']},{log['to']},{log['amount']:.{decimals}f}")
                print(f'{len(logs)} logs for range {block} to {block + chunkSize}', file=sys.stderr)
                break
            except requests.exceptions.RequestException as ex:
                attempts += 1
                if attempts > 3:
                    raise ex
                else:
                    print (f'Error getting logs from Infura {ex}, retrying', file=sys.stderr)


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
    parser.add_argument('-s', '--chunk-size', help='Number of blocks per eth_getLogs request (default 50000)', default=50000, type=int)
    parser.add_argument('-t', '--transfers', help='Print transfer events (default print address balances)', default=False, action='store_true')
    parser.add_argument('-c', '--csv', help='Output CSV (default JSON)', default=False, action='store_true')
    arguments = parser.parse_args()

    if arguments.transfers:
        if arguments.csv:
            printTransferEventLogsCSV(arguments.contract, arguments.decimals, chunkSize=arguments.chunk_size)
        else:
            tx = getTransferEventLogs(arguments.contract, arguments.decimals, chunkSize=arguments.chunk_size)
            print(json.dumps(tx, indent=4))
    else:
        balances = getBalances(tx)
        if arguments.csv:
            print('\n'.join([f'{x},{y}' for x, y in balances.items()]))
        else:
            print(json.dumps(balances, indent=4))
