from web3 import Web3

class BananaGunTrader:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))
    
    def execute_trade(self, pair_data, side):
        signed_tx = self._sign_transaction({
            'chain': pair_data['chainId'],
            'pair': pair_data['pairAddress'],
            'side': side.upper(),
            'amount': self._calculate_size(pair_data)
        })
        return self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

    def _calculate_size(self, pair_data):
        balance = self.w3.eth.get_balance(Config.WALLET_ADDRESS)
        return min(
            Config.RISK_PER_TRADE * balance,
            pair_data['liquidity'] * 0.05
        )