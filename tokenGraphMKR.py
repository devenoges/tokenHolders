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

import argparse, os, sys
from collections import defaultdict
from decimal import Decimal

import simplejson as json
import numpy as np
import matplotlib.pyplot as plt

import tokenHolders

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

def plotMKR(output, blocks, mkr, mkrOld, mkrBoth, gini, giniP1, gini1):
    fig, ax1 = plt.subplots()

    red = 'tab:red'
    blue = 'tab:blue'
    #x_tick_spacing = 500000 #blocks

    ax1.set_xlabel('Block')
    #ax1.xaxis.set_major_locator(ticker.MultipleLocator(x_tick_spacing))
    ax1.plot(blocks, mkr, color='tab:orange', label='MKR')
    ax1.plot(blocks, mkrBoth, color='tab:pink', label='MKR + MKR_OLD')
    ax1.plot(blocks, mkrOld, color=red, label='MKR_OLD')

    ax1.set_ylabel('Holders', color=red)
    ax1.tick_params(axis='y', labelcolor=red)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
    ax1.set_xticks(ax1.get_xticks()[::2]) # display every 2nd x axis block tick
    ax2.set_ylim(0.89, 0.98)

    ax2.plot(blocks, gini, color='navy', label='All MKR')
    ax2.plot(blocks, giniP1, color=blue, label='0.1 MKR cutoff')
    ax2.plot(blocks, gini1, color='royalblue', label='1 MKR cutoff')

    ax2.set_ylabel('Gini', color=blue)  # already handled the x-label with ax1
    ax2.tick_params(axis='y', labelcolor=blue)

    # add empty plots to create combined legend
    ax2.plot(np.nan, 'orange', label='MKR')
    ax2.plot(np.nan, red, label='MKR_OLD')
    ax2.plot(np.nan, 'pink', label='MKR + MKR_OLD')

    plt.title('MKR Holders and Gini Index')
    plt.legend(loc='upper left')
    #plt.legend(loc='lower center')
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.savefig(output)

def historyMKR(output, mkrTransOld, mkrTrans, days=None, verbose=False, giniBoth=False, giniOld=False):
    #excluded addresses
    foundationMultisig = '0x7bb0b08587b8a6b8945e09f1baca426558b0f06a'
    redeamerContract = '0x642ae78fafbb8032da552d619ad43f1d81e4dd7c'
    dsChief = '0x8e2a84d6ade1e7fffee039a35ef5f19f13057152'
    creation = '0x731c6f8c754fa404cfcc2ed8035ef79262f65702'
    creationOld = '0xe02640be68df835aa3327ea6473c02c8f6c3815a'
    excludedAddresses = [foundationMultisig, redeamerContract, dsChief, creation, creationOld]

    mkrTransBoth = sorted(mkrTransOld + mkrTrans, key=lambda x: int(x['blockNumber'], 16))
    start = int(mkrTransBoth[0]['blockNumber'], 16)
    finish = int(mkrTransBoth[-1]['blockNumber'], 16)
    blocksPerDay = 5760
    if verbose:
        print(f'First block {start}, last block {finish}, step {blocksPerDay} blocks', file=sys.stderr)

    b, m, mo, mb = [], [], [], []
    g = [[], [], []]
    for toBlock in range(start, finish+1, blocksPerDay):
        balsNew = tokenHolders.getBalances(mkrTrans, toBlock)
        balsOld = tokenHolders.getBalances(mkrTransOld, toBlock)
        balsBoth = tokenHolders.getBalances(mkrTransBoth, toBlock)

        if giniBoth:
            bals = balsBoth
        elif giniOld:
            bals = balsOld
        else:
            bals = balsNew

        if verbose:
            print(f'block: {toBlock} holders Old: {len(balsOld)} new: {len(balsNew)} both: {len(balsBoth)}', file=sys.stderr)

        empty = False
        for i, cutoff in enumerate(['0', '0.1', '1']):
            cutoff = Decimal(cutoff)
            balsCutoff = np.array([x['amount'] for x in bals if x['address'] not in excludedAddresses and x['amount'] >= cutoff])
            if not balsCutoff.any():
                empty = True
                continue
            g[i].append(gini(balsCutoff))

        if not empty:
            b.append(toBlock)
            m.append(len(balsNew))
            mo.append(len(balsOld))
            mb.append(len(balsBoth))

    if days is not None:
        plotMKR(output, b[-days:], m[-days:], mo[-days:], mb[-days:], g[0][-days:], g[1][-days:], g[2][-days:])
    else:
        plotMKR(output, b, m, mo, mb, g[0], g[1], g[2])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='tokenGraphMKR.py')
    parser.add_argument('-v', '--verbose', help='Show processing messages', action='store_true', default=False)
    parser.add_argument('-t', '--transfer-log', help='JSON log file of ERC20 transfer events', type=str, required=True)
    parser.add_argument('-o', '--transfer-log-old', help='JSON log file of old ERC20 transfer events', type=str, required=True)
    parser.add_argument('-d', '--days', help='Number of days to plot, default all', type=int, default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-b', '--gini-both', action='store_true', help='Graph Gini for both MKR and MKR_OLD (default MKR only)', default=False)
    group.add_argument('-l', '--gini-old', action='store_true', help='Graph MKR_OLD only', default=False)
    parser.add_argument('output', help='Output_filename', type=str)
    arguments = parser.parse_args()

    txs = []
    for log in [arguments.transfer_log_old, arguments.transfer_log]:
        tx = json.load(open(log, 'r'), use_decimal=True)
        txs.append(tx)
        if arguments.verbose:
            print(f'Read {len(tx)} transfer events from {log}', file=sys.stderr)

    historyMKR(arguments.output, *txs, days=arguments.days,
            verbose=arguments.verbose, giniOld=arguments.gini_old, giniBoth=arguments.gini_both)

