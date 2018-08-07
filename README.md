# tokenHolders.py

Get Ethereum ERC20 Transfer Event Logs with Infura, graph basic ownership stats.


![graph](https://github.com/devenoges/tokenHolders/raw/master/MKR_Holders_and_Gini_Index_for_MKR_only.png "MKR Holders and Gini Index for MKR only")


## Installation

This project uses *Python 3.6.6*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/devenoges/tokenHolders.git
pip3 install -r requirements.txt
```


## Usage

To produce the graphs above:
```
$ export INFURA_API_KEY=<your-infura-api-key>
$ ./tokenHolders.py -t 0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2 > tx.MKR.json
$ ./tokenHolders.py -t 0xC66eA802717bFb9833400264Dd12c2bCeAa34a6d > tx.MKR_OLD.json
$ ./tokenGraphMKR.py -t tx.MKR.json -o tx.MKR_OLD.json MKR.png
```
```
tokenHolders.py [-h] [-d DECIMALS] [-t] contract

Requires the environment variable INFURA_API_KEY to be set.

positional arguments:
  contract              ERC20 contract address

optional arguments:
  -h, --help            show this help message and exit
  -d DECIMALS, --decimals DECIMALS
                        ERC20 contract decimals (default 18)
  -t, --transfers       Print transfer events (default print address balances)

e.g. INFURA_API_KEY=<Your-Infura-Key> ./tokenHolders.py 0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2 > MKR_bal.json
```

```
tokenGraphMKR.py [-h] [-v] [-d DAYS] -t TRANSFER_LOG -o TRANSFER_LOG_OLD
                        (-b | -l) output

positional arguments:
  output                Output_filename

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Show processing messages
  -d DAYS, --days DAYS  Number of days to plot, default all
  -t TRANSFER_LOG, --transfer-log TRANSFER_LOG
                        JSON log file of ERC20 transfer events
  -o TRANSFER_LOG_OLD, --transfer-log-old TRANSFER_LOG_OLD
                        JSON log file of old ERC20 transfer events
  -b, --gini-both       Graph Gini for both MKR and MKR_OLD (default MKR only)
  -l, --gini-old        Graph MKR_OLD only
```
