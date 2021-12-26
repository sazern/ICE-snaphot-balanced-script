import time
import json
import getpass
from iconsdk.builder.call_builder import Call, CallBuilder
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.builder.transaction_builder import (
    TransactionBuilder,
    DeployTransactionBuilder,
    CallTransactionBuilder,
    MessageTransactionBuilder
)

nid = IconService(HTTPProvider("https://ctz.solidwallet.io/api/v3"))
icon_service = IconService(HTTPProvider("https://ctz.solidwallet.io/api/v3"))
EXA = 10**18

BALN_LOAN_CONTRACT = "cx66d4d90f5f113eba575bf793570135f9b10cece1"
GOV_CONTRACT = "cx0000000000000000000000000000000000000000"

sicxamounthex = ""
sicxamountstr = ""
sicxamountint = ""

contracts = {
    "loans": {'SCORE': "cx66d4d90f5f113eba575bf793570135f9b10cece1"},
    "dex": {'SCORE': "cxa0af3165c08318e988cb30993b3048335b94af6c"},
    "sicx": {'SCORE': "cx2609b924e33ef00b648a409245c7ea394c467824"},
    "bnUSD": {'SCORE': "cx88fd7df7ddff82f7cc735c871dc519838cb235bb"}
}
print("########################## MAINNET VERSION ##########################")
print("Use at your own risk, i dont take any responsability for lost funds")
print("########################## MAINNET VERSION ##########################")

name = input("enter keystore filename: ")
pw = getpass.getpass("Enter Password: ")
wallet = KeyWallet.load(name, pw)
adress = wallet.get_address()
balance = icon_service.get_balance(adress)
convbalance = balance / 10**18
strbalance = str(convbalance)
print("### Wallet loaded ###")
print("Address: ", adress)
print("Balance: " + strbalance + " ICX")
print ("############################################")

decimal = int(input("Amount of BNUSD you want to borrow: "))
convdecimal = decimal * EXA
tohex = hex(convdecimal)
strdecimal = str(decimal)
print("############################################")

bnusd = int(input("Amount of BNUSD you want to swap to sICX before snapshot "))
convbnusd = bnusd * EXA
bnusdtohex = hex(convbnusd)
strbnusd = str(bnusd)
print("############################################")


startblock = ""
endblock = ""
block = ""


def first_check():
    global block
    block = icon_service.get_block("latest")["height"]
    block_height = str(block)
    print("Current block height: " + block_height)
    print("############################################")
    global startblock
    global endblock
    startblock = int(input("Enter blockheight you want to take the loan at: "))
    print("############################################")
    endblock = int(input("Enter blockheight you want to swap back to bnusd and repay the loan at: "))
    print("### BOT STARTED ###")

def check_block():
    global block
    block = icon_service.get_block("latest")["height"]
    block_height = str(block)
    print("Current block height: " + block_height)
        
    while block <= startblock:
        check_block()
    if block >= startblock:
        borrow()

def borrow():
    print("### Borrowing bnUSD ###")
    Borrow_bnusd = CallTransactionBuilder().from_(adress)\
                    .to(BALN_LOAN_CONTRACT)\
                    .method("depositAndBorrow")\
                    .nid(1)\
                    .params({"_asset": "bnUSD", "_amount": tohex})\
                    .build()
    estimate_step = icon_service.estimate_step(Borrow_bnusd)
    step_limit = estimate_step + 10000
    signed_transaction = SignedTransaction(Borrow_bnusd, wallet, step_limit)
    tx_hash = icon_service.send_transaction(signed_transaction)
    print("wait 5 sec")
    time.sleep(6)
    txresult = icon_service.get_transaction_result(tx_hash)
    print("transaction status (1:success, 0:failure): ", txresult["status"])
    print("borrowed " + strdecimal + " bnusd")
    swapbnusdtosicx()


def swapbnusdtosicx():

    

    print("### Swapping " + strbnusd + "bnUSD to sICX ###")
    to_token = contracts['sicx']['SCORE']
    params_data = "{\"method\": \"_swap\", \"params\": {\"toToken\":\"" + str(to_token) + "\", \"maxSlippage\":190}}"
    data = params_data.encode("utf-8")
    params = {'_to': contracts['dex']['SCORE'], '_value': bnusdtohex, '_data': data}
    transaction = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(contracts['bnUSD']['SCORE'])\
        .value(0)\
        .step_limit(10000000)\
        .nid(1)\
        .nonce(100)\
        .method("transfer")\
        .params(params)\
        .build()
    signed_transaction = SignedTransaction(transaction, wallet)
    tx_hash = icon_service.send_transaction(signed_transaction)
    print(tx_hash)
    print("wait 5 sec")
    time.sleep(6)
    txresult = icon_service.get_transaction_result(tx_hash)
    result2 = txresult["eventLogs"][3]
    global sicxamounthex
    global sicxamountint
    global sicxamountstr
    sicxamounthex = result2["data"][5]
    sicxamountdec = int(sicxamounthex, 16)
    sicxamountint = sicxamountdec / EXA
    sicxamountstr = str(sicxamountint)
    print(strbnusd + " bnUSD Swapped for " + sicxamountstr + " sICX")
    repay_block()

def repay_block():
    block = icon_service.get_block("latest")["height"]
    block_height = str(block)
    print("Current block height: " + block_height)
        
    while block <= endblock:
        repay_block()
    if block >= endblock:
        sicxtobnusd()

def sicxtobnusd():
    print("### Swapping sicx for bnusd ###")
    global sicxamounthex
    to_token = contracts['bnUSD']['SCORE']
    params_data = "{\"method\": \"_swap\", \"params\": {\"toToken\":\"" + str(to_token) + "\", \"maxSlippage\":190}}"
    data = params_data.encode("utf-8")
    params = {'_to': contracts['dex']['SCORE'], '_value': sicxamounthex, '_data': data}
    transaction = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(contracts['sicx']['SCORE'])\
        .value(0)\
        .step_limit(10000000)\
        .nid(1)\
        .nonce(100)\
        .method("transfer")\
        .params(params)\
        .build()
    signed_transaction = SignedTransaction(transaction, wallet)
    tx_hash = icon_service.send_transaction(signed_transaction)
    print(tx_hash)
    print("wait 5 sec")
    time.sleep(6)
    txresult = icon_service.get_transaction_result(tx_hash)
    result2 = txresult["eventLogs"][3]
    bnusdamounthex = result2["data"][5]
    bnusdamountdec = int(bnusdamounthex, 16)
    bnusdamountint = bnusdamountdec / EXA
    bnusdamountstr = str(bnusdamountint)
    print(sicxamountstr + " sicx Swapped for " + bnusdamountstr + " bnusd")
    repay_loan()

def repay_loan():
    print("### Repaying Loan ###")
    repay_bnusd = CallTransactionBuilder().from_(adress)\
        .to(BALN_LOAN_CONTRACT)\
        .method("returnAsset")\
        .params({"_symbol": "bnUSD", "_value": tohex})\
        .nid(1)\
        .build()
    estimate_step = icon_service.estimate_step(repay_bnusd)
    step_limit = estimate_step + 10000
    signed_transaction = SignedTransaction(repay_bnusd, wallet, step_limit)
    tx_hash = icon_service.send_transaction(signed_transaction)
    print("wait 5 sec")
    time.sleep(6)
    txresult = icon_service.get_transaction_result(tx_hash)
    print("repay transaction status (1:success, 0:failure): ", txresult["status"])
    print("Loan repayed")
    print("### EXITING ###")
    exit()



first_check()
check_block()


    