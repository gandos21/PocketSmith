# Pocketsmith automation
# Created based using REST APIs provided by Pocketsmith. Link to API documentation: https://developers.pocketsmith.com/
#  G Yoga - gyalias@yogarajah.net
import requests
import json
from WindowLayout import WindowFields as wf
from datetime import datetime
import MyUtils as ut

#### Configs & Globals ####
approvedTransFile = 'ApprovedTransactions.json'
keyFile = 'keyFile.json'
APPROVED_TRANS_HISTORY_DURATION = 15       # Number of days to keep approved transaction data in history file

headers = {
    "Accept": "application/json",
    "X-Developer-Key": ""
}
post_headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-Developer-Key": ""
}

categoryList = []
categoryIdLookup = {}

accountList = []
accountIdLookup = {}

#### End Configs & globals ####

# Read developer key from an external file. Returns True if a key is read, False otherwise
def ReadDevKey():
    # Load developer key from key file
    try:  # If file exist, load data from file, otherwise start with a new history file
        with open(keyFile, 'r') as fp:
            apiKey = json.load(fp)['ApiKey']
        if len(apiKey) != 128:      # Length of developer ksy is 128 bytes
            print('Invalid key length!')
            raise Exception

        headers['X-Developer-Key'] = apiKey
        post_headers['X-Developer-Key'] = apiKey
        return True
    except:
        keyDict = {}
        keyDict['ApiKey'] = ''
        try:    # Create an empty key file
            with open(keyFile, 'w') as fp:
                json.dump(keyDict, fp, indent=4)
        except:
            print(f'Error creating key file {keyFile}')
        else:
            # A developer key can be from Pocketsmith settings menu (Security & connections -> Manage developer keys)
            print(f'Pocketsmith developer API key not found! Obtain and save a key in {keyFile}')
        return False


# Function to get get user data from Pocketsmith account
def GetUserId():
    url = "https://api.pocketsmith.com/v2/me"
    response = requests.request("GET", url, headers=headers)
    userData = json.loads(response.text)
    return userData['id']

# Function to load categories and their IDs from Pocketsmith account
def LoadCategories():
    global categoryList
    global categoryIdLookup

    url = f'https://api.pocketsmith.com/v2/users/{GetUserId()}/categories'
    categories = json.loads(requests.request("GET", url, headers=headers).text)
    for i in categories:
        if 'Hidden' in i['title']:
            break       # Skip anything after this Hidden categories
        # Collect category names into a list and also make a dictionary to lookup category IDs
        if len(i['children']) == 0:     # If no children sub-categories, then save parent category name
            categoryList.append(i['title'])
        categoryIdLookup[i['title']] = i['id']
        for j in i['children']:
            #x = i['title'] + '->' + j['title']  # When saving child category, prefix with parent
            x = j['title']                       # Saving only child category
            categoryList.append(x)
            categoryIdLookup[x] = j['id']
    return

# Function to load all account and their IDs from Pocketsmith account
def LoadAccounts():
    global accountList
    global accountIdLookup

    # Get transaction accounts and their IDs. Note, there are 2 IDs associated with accounts: id and account_id. We need to use id to create or update transactions in them
    url = f'https://api.pocketsmith.com/v2/users/{GetUserId()}/transaction_accounts'
    accounts = json.loads(requests.request("GET", url, headers=headers).text)
    for i in accounts:
        #print('id: ', i['id'], ' --- ', 'account_id: ', i['account_id'], ' --- ', i['name'])
        accountList.append(i['name'])
        accountIdLookup[i['name']] = i['id']
    return

# Function to create new transaction. Used for both manual entry and to create initial split transactions
def PostTransaction(GuiPanelValues, Need_Review=True, ChangePayeeName=True):
    transAccountId = accountIdLookup[GuiPanelValues[wf.AC_FROM]]  # Account to post to
    url = f'https://api.pocketsmith.com/v2/transaction_accounts/{transAccountId}/transactions'
    payload = {
        'payee'       : GuiPanelValues[wf.PAYEE_NAME],
        'amount'      : '%.2f' % float(GuiPanelValues[wf.AMOUNT].replace(',','')),         # float() doesn't take comma separators, so removing them before converting to float. We added , separator to show on the GUI
        'date'        : GuiPanelValues[wf.TRANSACTION_DATE],
        'category_id' : categoryIdLookup[GuiPanelValues[wf.CATEGORY_NAME]],
        'note'        : GuiPanelValues[wf.NOTE_TEXT],
        'needs_review': Need_Review
        # Note: when transactions are created, they are always set for review by Pocketsmith.
        #   So even if we call this function with Need_Review=False, transaction will still come up for review
    }
    # If an account given for TransferTo, then make double entry: debit transaction on one account, credit on other
    if len(GuiPanelValues[wf.AC_TO]) and GuiPanelValues[wf.AC_TO] != GuiPanelValues[wf.AC_FROM]:
        # Double account entry
        # Update Payee name to 'Transfer : xxxx'
        # Check applicable for primary transaction only. For the other double entry, we will use 'Transfer : xxx' payee name.
        #   When ChangePayeeName is False, Payee is not changed when split trans are created for the first time as we want to clone the payee name of the original trans.
        #   We then change it with UpdateSplitTranferTransactions()
        if ChangePayeeName:
            payload['payee'] = 'Transfer : ' + GuiPanelValues[wf.AC_TO]
        response1 = requests.request("POST", url, json=payload, headers=post_headers)

        transAccountId = accountIdLookup[GuiPanelValues[wf.AC_TO]]        # Account to post to
        payload['payee'] = 'Transfer : ' + GuiPanelValues[wf.AC_FROM]
        payload['amount'] = '%.2f' % (float(GuiPanelValues[wf.AMOUNT].replace(',','')) * -1)   # Negate the amount for Transfer To account
        url = f'https://api.pocketsmith.com/v2/transaction_accounts/{transAccountId}/transactions'
        response2 = requests.request("POST", url, json=payload, headers=post_headers)
    else:
        # Single account entry
        response1 = requests.request("POST", url, json=payload, headers=post_headers)
        response2 = ''

    if str(response1) == '<Response [201]>' and str(response2) in ['', '<Response [201]>']:
        msg = 'Transaction posting success'
        res1 = json.loads(response1.text)
        if response2 != '':
            res2 = json.loads(response2.text)
        else:
            res2 = ''
    else:
        msg = f'Transaction posting failed! Res1: {str(response1)}, Res2: {str(response2)}'
        res1 = res2 = ''
        if str(response1) != '<Response [201]>':
            print(response1)
        if str(response2) not in ['', '<Response [201]>']:
            print(response2)
    print(msg)
    return res1, res2, msg


# Function to update main transaction and to create TransferTo transaction if required
def UpdateTransaction(TransactionId, GuiPanelValues, Need_Review=True):
    url = f'https://api.pocketsmith.com/v2/transactions/{TransactionId}'
    payload = {
        # Note: If amount and Payee Name are changed from original entry of the trans, then the updated trans will again come up for review, even if needs_review is updated with False
        #  We need to once again update it with only needs_review set to False. To confirm again, we use ConfirmTransaction()
        'payee'         : GuiPanelValues[wf.PAYEE_NAME],
        'amount'        : '%.2f' % float(GuiPanelValues[wf.AMOUNT].replace(',','')),           # float() doesn't take comma separators, so removing them before converting to float. We added , separator to show on the GUI
        'category_id'   : categoryIdLookup[GuiPanelValues[wf.CATEGORY_NAME]],
        'note'          : GuiPanelValues[wf.NOTE_TEXT],
        'needs_review'  : Need_Review
    }

    # If an account given for TransferTo, then make double entry: debit transaction on one account, credit on other
    if len(GuiPanelValues[wf.AC_TO]) and GuiPanelValues[wf.AC_TO] != GuiPanelValues[wf.AC_FROM]:
        # Double account entry
        # Update Payee name to 'Transfer : xxxx'
        payload['payee'] = 'Transfer : ' + GuiPanelValues[wf.AC_TO]
        response1 = requests.request("PUT", url, json=payload, headers=post_headers)           # Update existing transaction

        # Create a new transaction in TransferTo account
        transAccountId = accountIdLookup[GuiPanelValues[wf.AC_TO]]        # Account to post to
        url = f'https://api.pocketsmith.com/v2/transaction_accounts/{transAccountId}/transactions'
        payload['date'] = GuiPanelValues[wf.TRANSACTION_DATE]
        payload['payee'] = 'Transfer : ' + GuiPanelValues[wf.AC_FROM]
        payload['amount'] = '%.2f' % (float(GuiPanelValues[wf.AMOUNT].replace(',','')) * -1)   # Negate the amount for Transfer To account
        response2 = requests.request("POST", url, json=payload, headers=post_headers)
        if str(response2) == '<Response [201]>':
            # We need to re-run Update transaction API on the newly created transaction on TransferTo account to prevent that from appearing for confirmation
            payload2 = {'needs_review': False}
            transId = json.loads(response2.text)['id']
            url = f'https://api.pocketsmith.com/v2/transactions/{transId}'
            response2 = requests.request("PUT", url, json=payload2, headers=post_headers)  # Update existing transaction
    else:
        # Single account entry
        response1 = requests.request("PUT", url, json=payload, headers=post_headers)            # Update existing transaction
        response2 = ''

    if str(response1) == '<Response [200]>' and str(response2) in ['', '<Response [200]>']:     # Positive responses: 200 received for Update Transaction API, 201 for Create Transaction
        msg = 'Transaction posting success'
        res1 = json.loads(response1.text)
        if response2 != '':
            res2 = json.loads(response2.text)
        else:
            res2 = ''
    else:
        msg = f'Transaction posting failed! Res1: {str(response1)}, Res2: {str(response2)}'
        res1 = res2 = ''
        if str(response1) != '<Response [200]>':
            print(response1)
        if str(response2) not in ['', '<Response [200]>']:
            print(response2)
    return res1, res2, msg


# Function to split transactions
def UpdateSplitTranferTransactions(TransactionId1, TransactionId2, GuiPanelValues):
    url = f'https://api.pocketsmith.com/v2/transactions/{TransactionId1}'
    payload = {'needs_review' : False}

    # If an account given for TransferTo, then make double entry: debit transaction on one account, credit on other
    if len(GuiPanelValues[wf.AC_TO]) and GuiPanelValues[wf.AC_TO] != GuiPanelValues[wf.AC_FROM]:
        # Double account entry
        # Clear the first entry
        payload['payee'] = 'Transfer : ' + GuiPanelValues[wf.AC_TO]
        response1 = requests.request("PUT", url, json=payload, headers=post_headers)           # Update existing transaction

        # Clear the second entry
        url = f'https://api.pocketsmith.com/v2/transactions/{TransactionId2}'
        payload2 = {'needs_review' : False}     # Just clearing the review flag for the second transaction
        response2 = requests.request("PUT", url, json=payload2, headers=post_headers)  # Update existing transaction
    else:
        # Single account entry
        response1 = requests.request("PUT", url, json=payload, headers=post_headers)            # Update existing transaction
        response2 = ''

    if str(response1) == '<Response [200]>' and str(response2) in ['', '<Response [200]>']:     # Positive responses: 200 received for Update Transaction API, 201 for Create Transaction
        msg = 'Transaction posting success'
        res1 = json.loads(response1.text)
        if response2 != '':
            res2 = json.loads(response2.text)
        else:
            res2 = ''
    else:
        msg = f'Transaction posting failed! Res1: {str(response1)}, Res2: {str(response2)}'
        res1 = res2 = ''
        if str(response1) != '<Response [200]>':
            print(response1)
        if str(response2) not in ['', '<Response [200]>']:
            print(response2)
    return res1, res2, msg


# Function to confirm a transaction after it has been updated or created
def ConfirmTransaction(TransactionId):
    url = f'https://api.pocketsmith.com/v2/transactions/{TransactionId}'
    payload = {
        # Note: If amount and Payee Name are changed from original entry of the trans, then the updated trans will again come up for review, even if needs_review is updated with False
        #  We update transaction once again with this function only to set needs_review to False
        'needs_review' : False
    }
    response = requests.request("PUT", url, json=payload, headers=post_headers)            # Update existing transaction

    if str(response) == '<Response [200]>':     # Positive responses: 200 received for Update Transaction API, 201 for Create Transaction
        msg = 'Transaction posting success'
        res = json.loads(response.text)
    else:
        msg = f'Transaction confirmation failed! Res: {str(response)}'
        res = ''
        if str(response) != '<Response [200]>':
            print(response)
    return res, msg

# Function to confirm a transaction with payee update. Used to auto clear transactions that come back for re-approval. Payee is updated in case we previously update payee name to something else eg. 'Transfer : xxx'
def ConfirmTransactionWithPayee(TransactionId, PayeeName):
    url = f'https://api.pocketsmith.com/v2/transactions/{TransactionId}'
    payload = {
        # Note: If amount and Payee Name are changed from original entry of the trans, then the updated trans will again come up for review, even if needs_review is updated with False
        #  We update transaction once again with this function only to set needs_review to False
        'payee': PayeeName,
        'needs_review' : False
    }
    response = requests.request("PUT", url, json=payload, headers=post_headers)            # Update existing transaction

    if str(response) == '<Response [200]>':     # Positive responses: 200 received for Update Transaction API, 201 for Create Transaction
        msg = 'Transaction posting success'
        res = json.loads(response.text)
    else:
        msg = f'Transaction confirmation failed! Res: {str(response)}'
        res = ''
        if str(response) != '<Response [200]>':
            print(response)
    return res, msg


# Get all transactions for user. Each query retrieves a page of 30 transactions
def GetUserTransactions():
    # Get latest transactions
    url = f"https://api.pocketsmith.com/v2/users/{GetUserId()}/transactions"
    querystring = {"page": "1"}                                                         # FIXME - update code to get last 1month transactions, not just 1 page
    transactions = json.loads(requests.request("GET", url, headers=headers, params=querystring).text)
    unconfirmedTrans = []
    for i in transactions:
        if i['needs_review'] == True:       # Only collect unconfirmed transactions
            t = {}
            t['id'] = i['id']
            t['date'] = i['date']
            t['amount'] = i['amount']
            t['payee'] = i['payee']
            t['note'] = i['note']
            if i['category'] == None:       # Uncategorised transaction
                t['category'] = '<< Uncategorised >>'
            else:
                t['category'] = i['category']['title']
            t['account'] = i['transaction_account']['name']
            unconfirmedTrans.append(t)
    # if len(unconfirmedTrans) == 0:
    #     print('There are no new transactions to review')
    print('Recent 30 transactions:')
    for i in transactions:
        # Pad spaces information to vertically align them
        upSource = i['upload_source'] + ' ' * (9 - len(i['upload_source']))
        status = i['status'] + ' ' * (7 - len(i['status']))
        amt = '${:>11}'.format('{:,.2f}'.format(i['amount']))          # Currency formatting with right justification. Ref: https://stackoverflow.com/a/42658877
        PAYEE_LEN_MAX = 40
        payee = (i['payee'] + ' ' * (PAYEE_LEN_MAX - len(i['payee']))) if len(i['payee']) < PAYEE_LEN_MAX else i['payee'][:PAYEE_LEN_MAX]
        NOTE_LEN_MAX = 40
        note = (' ' * NOTE_LEN_MAX) if i['note'] is None else (i['note'] + ' ' * (NOTE_LEN_MAX - len(i['note']))) if len(i['note']) < NOTE_LEN_MAX else i['note'][:NOTE_LEN_MAX]
        print(f" {i['id']} | {'  New   ' if i['needs_review'] else 'Approved'} | {i['date']} | {upSource} | {status} | {amt} | {payee} | {note} |")

    return CheckNewTransactionsForReapproval(unconfirmedTrans), transactions


# Function to check new transactions come up for approval were previously approved or not. If approved, and data did not change, auto clear them
def CheckNewTransactionsForReapproval(UnconfirmedTrans):
    reapprovalCheck = False
    ApprovedTransDict = LoadApprovedTransactions()      # Load approved transactions from json history. Note, when data is read back from json, keys will be of string type. So we use str() to convert int keys when looking up data in ApprovedTransDict

    for idx, val in enumerate(UnconfirmedTrans):
        if str(val['id']) in ApprovedTransDict:
            # If transaction ID match, compare account, category and amount too. If they match auto clear the transaction
            if val['category'] == ApprovedTransDict[str(val['id'])][wf.CATEGORY_NAME] and \
                    val['account'] == ApprovedTransDict[str(val['id'])][wf.AC_FROM] and \
                    ut.IsFloatValueZero(val['amount'] - float(ApprovedTransDict[str(val['id'])][wf.AMOUNT].replace(',',''))):      # float() doesn't take comma separators, so removing them before converting to float

                res, status = ConfirmTransactionWithPayee(val['id'], ApprovedTransDict[str(val['id'])][wf.PAYEE_NAME])       #FIXME also recopy Category and Note
                reapprovalCheck = True
                print('\nTransaction:')
                print(f"  --> {ApprovedTransDict[str(val['id'])][wf.TRANSACTION_DATE]} | {ApprovedTransDict[str(val['id'])][wf.AC_FROM]} | {ApprovedTransDict[str(val['id'])][wf.AMOUNT]} | {ApprovedTransDict[str(val['id'])][wf.CATEGORY_NAME]} | {val['payee']}")
                if 'SUCCESS' in status.upper():
                    print(' had come up for re-approval and successfully auto cleared.\n')
                    UnconfirmedTrans.pop(idx)       # Remove it from unconfirmed transaction list
                else:
                    print(' auto clearing failed!\n')

    if not reapprovalCheck:
        print('\n - No transactions were auto cleared.\n')
    return UnconfirmedTrans


# Delete a transaction using ID. Or multi test transaction deleting function
def DeleteAccountTransaction(GuiPanelValues):
    transactionId = GuiPanelValues[wf.TRANSACTION_ID]
    if isinstance(transactionId, str):
        # Delete all test transactions created for script testing. Test transactions are transactions with "Test Trans" keyword in their Note field
        if 'TEST TRANS' in transactionId.upper():
            x, transactions = GetUserTransactions()
            print('---------------------------------------------')
            n = 0
            for i in transactions:
                if i['note'] is not None:
                    if 'TEST TRANS' in i['note'].upper():
                        url = f"https://api.pocketsmith.com/v2/transactions/{i['id']}"
                        response = requests.request("DELETE", url, headers=post_headers)
                        if str(response) == '<Response [204]>':
                            print('Deleted transaction:')
                            print(f"  {i['id']} | {i['date']} | {i['amount']} | {i['transaction_account']['name']} | {i['payee']} | {i['note']}")
                            n += 1
                        else:
                            print(f"Transaction {i['id']} deletion failed!  -> {response}")
            print(f'--- # of deleted transactions: {n} ---')
    else:
        # Individual transaction delete using transaction ID number
        url =f'https://api.pocketsmith.com/v2/transactions/{transactionId}'
        response =  requests.request("DELETE", url, headers=post_headers)
        if str(response) == '<Response [204]>':
            print(f'Transaction {transactionId} successfully deleted')
        else:
            print(f'Transaction {transactionId} deletion failed!  -> {response}')


# Function to get approved transaction from history file
def LoadApprovedTransactions():
    try:  # If file exist, load data from file, otherwise start with a new history file
        with open(approvedTransFile, 'r') as fp:
            approvedTrans = json.load(fp)
    except:
        approvedTrans = {}      # If json does not exist, start with an empty dictionary
    return approvedTrans

# Function to save approved transaction data to JSON file
def SaveApprovedTransaction(ApprovedTransDict):
    # Parse through the transaction dictionary and delete data that are older than APPROVED_TRANS_HISTORY_DURATION days
    removeKeyList = [k for k,v in ApprovedTransDict.items() if (datetime.now() - ut.StrToDate(v[wf.TRANSACTION_DATE])).days > APPROVED_TRANS_HISTORY_DURATION]
    for k in removeKeyList: del ApprovedTransDict[k]

    # Save to file
    try:
        with open(approvedTransFile, 'w') as fp:
            json.dump(ApprovedTransDict, fp, indent=4)  # Creating json with indentation. Ref: https://stackoverflow.com/a/12309296
    except:
        print(f'Error opening file {approvedTransFile} for update. Approved transaction not saved to history file!')
