# tokenHolders.py

Get Ethereum ERC20 Transfer Event Logs with Infura, graph basic ownership stats.

![graph](https://github.com/devenoges/tokenHolders/raw/master/MKR_Holders_and_Gini_Index_for_MKR_and_MKR_OLD.png "MKR Holders and Gini Index for MKR and MKR_OLD")


![graph](https://github.com/devenoges/tokenHolders/raw/master/MKR_Holders_and_Gini_Index_for_MKR_only.png "MKR Holders and Gini Index for MKR only")


## Installation

This project uses *Python 3.6.6*.

In order to clone the project and install required third-party packages please execute:
```
git clone https://github.com/devenoges/tokenHolders.git
pip3 install -r requirements.txt
```


## Usage

```
usage: tokenHolders.py [-h] [-d DECIMALS] [-t] contract

positional arguments:
  contract              ERC20 contract address

optional arguments:
  -h, --help            show this help message and exit
  -d DECIMALS, --decimals DECIMALS
                        ERC20 contract decimals (default 18)
  -t, --transfers       Print transfer events (default print address balances)

e.g. INFURA_API_KEY=<Your-Infura-Key> ./tokenHolders.py 0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2 > MKR_bal.json
```

