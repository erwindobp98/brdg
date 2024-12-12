from web3 import Web3
import time
import os
from concurrent.futures import ThreadPoolExecutor

# Detail jaringan dan data transaksi
networks = [
    {
        'name': 'arbitrum',
        'rpc_url': 'https://arb-sepolia.g.alchemy.com/v2/YhkuU2iX0rA1pk2F880RLF3ZiIpxmf6M',
        'chain_id': 421614,
        'contract_address': '0x8D86c3573928CE125f9b2df59918c383aa2B514D',
        'data': '0x56591d596273737000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000095036f0255c60d0cfc980a1fb19a2337aeabb75a00000000000000000000000000000000000000000000000000005ae1a15c8f380000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005af3107a4000'
    },
    {
        'name': 'base',
        'rpc_url': 'https://base-sepolia.g.alchemy.com/v2/_BAZscI7RzE4pfI8loukVwMuxtsg6Rye',
        'chain_id': 84532,
        'contract_address': '0x30A0155082629940d4bd9Cd41D6EF90876a0F1b5',
        'data': '0x56591d596f70737000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000003508E69F82117290E1237Fb39226ac6E9F7d00000000000000000000000000000000000000000000000000005ae1a1a613e80000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005af3107a4000'
    },
    {
        'name': 'blast',
        'rpc_url': 'https://blast-sepolia.g.alchemy.com/v2/SiRDe2sBrBR3f2vm3cbhNSYpqwnk5LwJ',
        'chain_id': 168587773,
        'contract_address': '0x1D5FD4ed9bDdCCF5A74718B556E9d15743cB26A2',
        'data': '0x56591d596273737000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000095036f0255c60d0cfc980a1fb19a2337aeabb75a00000000000000000000000000000000000000000000000000005ae1a15c8f380000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005af3107a4000'
    },
    {
        'name': 'optimism',
        'rpc_url': 'https://opt-sepolia.g.alchemy.com/v2/1Mt3x7piPJMANnB5TVjsHhBVxrVMKX9C',
        'chain_id': 11155420,
        'contract_address': '0xF221750e52aA080835d2957F2Eed0d5d7dDD8C38',
        'data': '0x56591d596273737000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000095036f0255c60d0cfc980a1fb19a2337aeabb75a00000000000000000000000000000000000000000000000000005ae1a15c8f380000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005af3107a4000'
    }
]

# Daftar private key dan alamat dompet
wallets = [
    {
        'private_key': 'ISI PRIVATE KEY',
        'address': 'ISI ADDRESS'
    }
]

def send_bridge_transaction(network, private_key, my_address):
    web3 = Web3(Web3.HTTPProvider(network['rpc_url']))
    if not web3.is_connected():
        print(f"Tidak dapat terhubung ke jaringan {network['name']}")
        return None

    nonce = web3.eth.get_transaction_count(my_address)
    
    # Check balance
    balance = web3.eth.get_balance(my_address)
    transaction_value = web3.to_wei(0.0001, 'ether')
    
    # Estimate gas
    try:
        gas_estimate = web3.eth.estimate_gas({
            'to': network['contract_address'],
            'from': my_address,
            'data': network['data'],
            'value': transaction_value
        })
        gas_limit = gas_estimate + 10000  # Tambahkan buffer gas
    except Exception as e:
        print(f"Error estimating gas: {e}")
        return None

    # Set reasonable gas price limits
    current_gas_price = web3.eth.gas_price
    max_priority_fee_per_gas = int(min(current_gas_price * 0.1, web3.to_wei(0.052, 'gwei')))
    max_fee_per_gas = int(current_gas_price + max_priority_fee_per_gas)

    # Check if the wallet has enough funds
    total_cost = transaction_value + (gas_limit * max_fee_per_gas)
    if balance < total_cost:
        print(f"Insufficient funds for transaction. Balance: {web3.from_wei(balance, 'ether')} ETH, Needed: {web3.from_wei(total_cost, 'ether')} ETH")
        return None

    # Create transaction
    transaction = {
        'nonce': nonce,
        'to': network['contract_address'],
        'value': transaction_value,
        'gas': gas_limit,
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee_per_gas,
        'chainId': network['chain_id'],
        'data': network['data']
    }

    # Sign transaction with private key
    try:
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    except Exception as e:
        print(f"Error signing transaction: {e}")
        return None

    # Send transaction
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return web3.to_hex(tx_hash)
    except Exception as e:
        print(f"Error sending transaction: {e}")
        return None

def process_wallet(wallet):
    successful_txs = 0
    private_key = wallet['private_key']
    my_address = wallet['address']
    
    try:
        network_index = 0
        while True:
            network = networks[network_index]
            tx_hash = send_bridge_transaction(network, private_key, my_address)
            if tx_hash:
                successful_txs += 1
                print(f"Network: {network['name']} | Tx Hash: {tx_hash} | Successful Tx: {successful_txs}")
            else:
                print(f"Transaction failed on network: {network['name']}")
            time.sleep(60)  # Tunggu 60 detik sebelum transaksi berikutnya
            network_index = (network_index + 1) % len(networks)
    except KeyboardInterrupt:
        print("Operasi dihentikan oleh pengguna.")
    except Exception as e:
        print(f"Terjadi kesalahan: {e}")

def main():
    with ThreadPoolExecutor(max_workers=len(wallets)) as executor:
        executor.map(process_wallet, wallets)

if __name__ == "__main__":
    main()
