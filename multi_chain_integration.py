import asyncio
from typing import Dict, List
from web3 import Web3
import aiohttp

class MultiChainIntegration:
    def __init__(self, config: Dict):
        self.chains = {}
        for chain_name, chain_config in config['chains'].items():
            self.chains[chain_name] = Web3(Web3.HTTPProvider(chain_config['rpc_url']))
            self.chains[chain_name].middleware_onion.inject(geth_poa_middleware, layer=0)  # For PoA chains
        
        self.dex_contracts = config['dex_contracts']
        self.bridge_contracts = config['bridge_contracts']

    async def get_token_balance(self, chain: str, token_address: str, wallet_address: str) -> float:
        w3 = self.chains[chain]
        token_contract = w3.eth.contract(address=token_address, abi=self.get_erc20_abi())
        balance = token_contract.functions.balanceOf(wallet_address).call()
        decimals = token_contract.functions.decimals().call()
        return balance / (10 ** decimals)

    async def get_token_price(self, chain: str, token_address: str, dex_address: str) -> float:
        w3 = self.chains[chain]
        dex_contract = w3.eth.contract(address=dex_address, abi=self.get_dex_abi())
        price = dex_contract.functions.getTokenPrice(token_address).call()
        return w3.from_wei(price, 'ether')

    async def swap_tokens(self, chain: str, from_token: str, to_token: str, amount: float, wallet: str) -> Dict:
        w3 = self.chains[chain]
        dex_contract = w3.eth.contract(address=self.dex_contracts[chain], abi=self.get_dex_abi())
        
        # Approve token spending
        token_contract = w3.eth.contract(address=from_token, abi=self.get_erc20_abi())
        approve_tx = token_contract.functions.approve(self.dex_contracts[chain], amount).build_transaction({
            'from': wallet,
            'nonce': w3.eth.get_transaction_count(wallet),
        })
        signed_approve_tx = w3.eth.account.sign_transaction(approve_tx, private_key=self.get_private_key(wallet))
        w3.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
        
        # Execute swap
        swap_tx = dex_contract.functions.swapExactTokensForTokens(
            amount,
            0,  # min amount out (set to 0 for simplicity, but should be calculated in production)
            [from_token, to_token],
            wallet,
            w3.eth.get_block('latest')['timestamp'] + 1200  # deadline: 20 minutes from now
        ).build_transaction({
            'from': wallet,
            'nonce': w3.eth.get_transaction_count(wallet),
        })
        signed_swap_tx = w3.eth.account.sign_transaction(swap_tx, private_key=self.get_private_key(wallet))
        tx_hash = w3.eth.send_raw_transaction(signed_swap_tx.rawTransaction)
        return {'transaction_hash': tx_hash.hex()}

    async def bridge_tokens(self, from_chain: str, to_chain: str, token: str, amount: float, wallet: str) -> Dict:
        w3_from = self.chains[from_chain]
        bridge_contract = w3_from.eth.contract(address=self.bridge_contracts[from_chain], abi=self.get_bridge_abi())
        
        # Approve token spending
        token_contract = w3_from.eth.contract(address=token, abi=self.get_erc20_abi())
        approve_tx = token_contract.functions.approve(self.bridge_contracts[from_chain], amount).build_transaction({
            'from': wallet,
            'nonce': w3_from.eth.get_transaction_count(wallet),
        })
        signed_approve_tx = w3_from.eth.account.sign_transaction(approve_tx, private_key=self.get_private_key(wallet))
        w3_from.eth.send_raw_transaction(signed_approve_tx.rawTransaction)
        
        # Execute bridge transaction
        bridge_tx = bridge_contract.functions.bridgeTokens(
            token,
            amount,
            to_chain,
            wallet
        ).build_transaction({
            'from': wallet,
            'nonce': w3_from.eth.get_transaction_count(wallet),
        })
        signed_bridge_tx = w3_from.eth.account.sign_transaction(bridge_tx, private_key=self.get_private_key(wallet))
        tx_hash = w3_from.eth.send_raw_transaction(signed_bridge_tx.rawTransaction)
        return {'transaction_hash': tx_hash.hex()}

    async def get_gas_price(self, chain: str) -> int:
        w3 = self.chains[chain]
        return w3.eth.gas_price

    async def estimate_gas(self, chain: str, from_address: str, to_address: str, data: str) -> int:
        w3 = self.chains[chain]
        return w3.eth.estimate_gas({
            'from': from_address,
            'to': to_address,
            'data': data,
        })

    async def get_cross_chain_opportunities(self) -> List[Dict]:
        opportunities = []
        tokens = ['USDC', 'USDT', 'WETH', 'WBTC']  # Example tokens
        
        for token in tokens:
            prices = {}
            for chain in self.chains:
                price = await self.get_token_price(chain, self.get_token_address(chain, token), self.dex_contracts[chain])
                prices[chain] = price
            
            for chain1 in prices:
                for chain2 in prices:
                    if chain1 != chain2:
                        price_diff = (prices[chain2] - prices[chain1]) / prices[chain1]
                        if abs(price_diff) > 0.01:  # 1% threshold
                            opportunities.append({
                                'token': token,
                                'from_chain': chain1,
                                'to_chain': chain2,
                                'price_difference': price_diff,
                                'potential_profit': price_diff * 1000  # Assuming 1000 USD trade size
                            })
        
        return sorted(opportunities, key=lambda x: abs(x['potential_profit']), reverse=True)

    def get_private_key(self, wallet: str) -> str:
        # In a real-world scenario, you would securely retrieve the private key
        # This is just a placeholder
        return "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

    def get_erc20_abi(self):
        # Return the ABI for ERC20 token contract
        pass

    def get_dex_abi(self):
        # Return the ABI for DEX contract
        pass

    def get_bridge_abi(self):
        # Return the ABI for bridge contract
        pass

    def get_token_address(self, chain: str, token: str) -> str:
        # Return the token address for the given chain and token symbol
        pass