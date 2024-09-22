from web3 import Web3
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class DEXIntegration:
    def __init__(self, config: Dict):
        self.w3 = Web3(Web3.HTTPProvider(config['rpc_url']))
        self.uniswap_router_address = config['uniswap_router_address']
        self.uniswap_router_abi = config['uniswap_router_abi']
        self.uniswap_router = self.w3.eth.contract(address=self.uniswap_router_address, abi=self.uniswap_router_abi)
        self.wallet_address = config['wallet_address']
        self.private_key = config['private_key']

    async def get_token_price(self, token_address: str, amount: int = 1) -> float:
        weth_address = self.uniswap_router.functions.WETH().call()
        try:
            amounts_out = self.uniswap_router.functions.getAmountsOut(
                amount,
                [token_address, weth_address]
            ).call()
            return amounts_out[1] / 1e18  # Convert to ETH
        except Exception as e:
            logger.error(f"Error getting token price: {str(e)}")
            return 0

    async def execute_swap(self, token_in: str, token_out: str, amount_in: int) -> Dict:
        try:
            deadline = self.w3.eth.get_block('latest')['timestamp'] + 300  # 5 minutes from now
            tx = self.uniswap_router.functions.swapExactTokensForTokens(
                amount_in,
                0,  # We don't specify a minimum amount out to simplify the example
                [token_in, token_out],
                self.wallet_address,
                deadline
            ).buildTransaction({
                'from': self.wallet_address,
                'nonce': self.w3.eth.get_transaction_count(self.wallet_address),
                'gas': 250000,
                'gasPrice': self.w3.eth.gas_price
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'status': 'success',
                'tx_hash': tx_hash.hex(),
                'gas_used': receipt['gasUsed']
            }
        except Exception as e:
            logger.error(f"Error executing swap: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }