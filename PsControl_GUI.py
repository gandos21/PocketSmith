# Pocketsmith py automation for transaction approval
#  This script was created to enhance new transactions confirmation process. Currently, transaction confirmation via PocketSmith doesn't provide a capability
#  to make a double entry transaction. For example, when you make an ATM withdrawal it comes via bank sync for confirmation on bank account. However, if we need to make
#  a matching transaction in Wallet account (manual account), we need to make a manual entry. Making manual entry is not intuitive via the standard web interface and it can be easily missed.
#  One of the aim of this script is to provide 'Transfer To' capability to automatically make an opposing transaction in the other manual accounts (eg. Wallet, Super Savings, etc).
#  When splitting transaction, providing separate Note text for each split transaction is also possible with this script.
#
# This file is the main entry point for the script.
#  Created using PySimepleGUI package. Template from window panel was taken from https://pysimplegui.readthedocs.io/en/latest/cookbook/
#  Repository link: https://github.com/gandos21/PocketSmith
import PySimpleGUI as sg
import sys
import WindowLayout as wl
import MyPocketSmith as ps
import MyUtils as ut

#### Constants, configs & globals ####
WIN_READ_TIMEOUT        = 1000      # Window read timeout duration in ms
NEW_DATA_CHECK_INTERVAL = 600       # Time interval in s to get new data from Pocketsmith

#### End Configs & globals ####

# Main function to start gui panel
def main():
    if not ps.ReadDevKey():     # Read developer API key from external file. If key file doesn't exist, terminate script
        return

    # Get list of categories and accounts from Pocketsmith
    ps.LoadCategories()
    ps.LoadAccounts()
    approvedTransactionDict = ps.LoadApprovedTransactions()
    unconfirmedTransactions, allTransactions = ps.GetUserTransactions()

    # Save the sys.stdout object pointer. With the window.read() call below, the stdout pointer will switch to the GUI output panel, because of the added sg.Output() element in the GUI layout. Ref: https://pysimplegui.readthedocs.io/en/latest/#output-element
    #  So any print() calls after that will appear on GUI only. Hence, we save the original stdout object pointer to print to command window for debugging purpose.  Ref: https://stackoverflow.com/a/3263733
    #  For example, to print anything to console after GUI is launched and window.read() is called, use the following, until sys.stdout and sys.stderr are re-instated
    #   cmdPrint.write(testVariable + '\n')     # Debug print to console. write() takes a string input. If testVariable is not string covert to string, like str(testVariable)
    cmdPrint = sys.stdout
    cmdErr = sys.stderr

    # Window colour theme
    #sg.theme('SandyBeach')
    sg.theme('LightGreen1')
    #print(sg.theme_list())     # Debug: Print all available themes in PySimpleGUI. Also check at, https://pysimplegui.readthedocs.io/en/latest/#themes-automatic-coloring-of-your-windows

    # Create the window object
    panel = wl.WindowLayout(ps.accountList, ps.categoryList, unconfirmedTransactions)
    #window = sg.Window('Pocketsmith Transaction Entry', window_layout, default_element_size=(80, 1), grab_anywhere=False)
    window = sg.Window('Pocketsmith Control', panel.layout(), grab_anywhere=False)
    #print(window.AllKeysDict)  # Debug: Print all dict keys. Found attribute using dir() function
    #print(dir(window[0]))      # Debug: Addresing the elements of window via dict keys. Ref: https://pysimplegui.readthedocs.io/en/latest/#windowfindelementkey-shortened-to-windowkey

    # Initial state of window elements' values will be panelDefaults
    fieldValuesCurrent = panel.fieldValues
    initialHideDone = False
    unconfirmedTransactionApproved = [False for i in range(len(unconfirmedTransactions))]
    unconfirmedTransactionAmount   = [float(v['amount']) for i, v in enumerate(unconfirmedTransactions)]
    hiddenSplitRow = [0 for i in range(len(unconfirmedTransactions))]       # List of integer counters initialised to 0. Counters to keep track of inserted split rows for each main transactions

    # If no new transactions to review at program launch, display a message and hide table title row
    NoReviewCheck(unconfirmedTransactions, window)

    # Main window event handler loop
    timerCount = NEW_DATA_CHECK_INTERVAL
    while True:
        if initialHideDone:
            event, values = window.read(timeout=WIN_READ_TIMEOUT)           # Read event from window. Buttons are event enabled. Events for other elements enabled (using parameter enable_events) as desired. Ref: https://pysimplegui.readthedocs.io/en/latest/#events

        else:  # Keep empty rows for split transaction until they are required
            event, values = window.read(timeout=50)         # A quicker read() with shorter timeout when window is newly created with new unhidden rows, so we hide them them quickly. Note: read() is a blocking call without a timeout, unless an event occurs
            for row in range(len(unconfirmedTransactions)):
                for i in range(1, panel.splitRowsCount):
                    window[f'-SplitRow_{row}_{i}-'].hide_row()          # Hint from https://github.com/PySimpleGUI/PySimpleGUI/issues/721#issuecomment-438704952
                window[f'-TransGrid_SpacerRow_{row}-'].hide_row()
            initialHideDone = True

        if event == '__TIMEOUT__' or event == '-ReviewDataRefresh-':
            timerCount -= 1
            # Debug: Print count down time on console
            cmdPrint.write('%4ds\b\b\b\b\b' % timerCount)     # Moving back the cursor 5 positions using \b, so that the 4 digit (works up to 9999s) count down value is written over the old one
            cmdPrint.flush()

            if timerCount == 0 or event == '-ReviewDataRefresh-':       # Every NEW_DATA_CHECK_INTERVAL seconds, check for new transactions from Pocketsmith. Or when Refresh button is clicked
                timerCount = NEW_DATA_CHECK_INTERVAL
                cmdPrint.write('Debug 1: Checking for new data' + '\n')
                #if False not in unconfirmedTransactionApproved:
                unconfirmedTransactions, allTransactions = ps.GetUserTransactions()
                if unconfirmedTransactionApproved.count(False) != len(unconfirmedTransactions):
                    cmdPrint.write('Debug 2: Downloaded new transactions for review' + '\n')
                    initialHideDone = False
                    unconfirmedTransactionApproved = [False for i in range(len(unconfirmedTransactions))]
                    unconfirmedTransactionAmount = [float(v['amount']) for i, v in enumerate(unconfirmedTransactions)]
                    hiddenSplitRow = [0 for i in range(len(unconfirmedTransactions))]  # List of integer counters initialised to 0. Counters to keep track of inserted split rows for each main transactions
                    # Close and re-open window with newly downloaded transaction data
                    window.close()
                    panel = wl.WindowLayout(ps.accountList, ps.categoryList, unconfirmedTransactions, fieldValues=fieldValuesCurrent)
                    window = sg.Window('Pocketsmith Control', panel.layout(), grab_anywhere=False)
                    event, values = window.read(timeout=50)       # Dummy initial read after window creation. A short timeout given because read() is normally a blocking call, unless an event occurs
                    NoReviewCheck(unconfirmedTransactions, window)
                    cmdPrint.write(str(unconfirmedTransactionApproved) + '\n')



        ## Exit button or window close (X) event ##
        if event in (sg.WIN_CLOSED, 'Exit'):    # Checking for window X close button or our own Exit button. Checking of X is prioritised over other events. Doing X abruptly stop compiled EXE execution, eg. doing json dump above this line was crashing compiled EXE when X was clicked.
            break                               #  When X is clicked to close, window object will return None values in 'values', i.e. no dictionaty values. event will be None too.

        ## Button events ##
        if event == 'Post':
            ps.PostTransaction(values)
            
        if event == 'Get Trans':
            pass    # TODO
            #ps.GetAccountTransactions(values)
        if event == 'Delete Tran':
            ps.DeleteAccountTransaction(values)
        if event == 'Clear Msg':
            window.FindElement('-Output-').Update('')   # Clearing the contents of Output element window. Ref: https://github.com/PySimpleGUI/PySimpleGUI/issues/1441#issuecomment-493741474
        if event == 'Clear Reports':
            pass
        ## File name input text box change events ##
        if event == '-TabGroup-':
            if values['-TabGroup-'] == 'Review':
                if False in unconfirmedTransactionApproved:
                    if len(unconfirmedTransactions) == 0:
                        window['-ReviewTab_Status-'].Update(' ' * 90 + 'No new transactions to review', text_color='darkblue', font='Any 12 bold')          # Using Update() to update the value of the InputText box.  Ref: https://pysimplegui.readthedocs.io/en/latest/call%20reference/#window/#Update
                    else:
                        window['-ReviewTab_Status-'].Update(' ' * 70 + 'Review & confirm new transactions. If Rejected, transaction will be deleted!', text_color='darkblue', font='Any 12 bold')
                        # Fill in the new transaction data to table
                        for i, row in enumerate(unconfirmedTransactions):
                            window[f'-TransGrid_{i}_0_0-'].Update(row['date'])
                            window[f'-TransGrid_{i}_1_0-'].Update(row['account'])
                            if float(row['amount']) < 0.0:
                                # Note: we use SepAmount() to add , separators to display on GUI.
                                #   This caused problem later when we needed to convert it to float as float() doesn't take , in string input.
                                #   So we later remove the comma whenever we convert GUI amount strings to float, using .replace(',','')
                                window[f'-TransGrid_{i}_2_0-'].Update(ut.SepAmount('%.2f' % float(row['amount'])), text_color='brown')     # Show debit amount in brown colour, credit in green
                            else:
                                window[f'-TransGrid_{i}_2_0-'].Update(ut.SepAmount('%.2f' % float(row['amount'])), text_color='green')
                            try:
                                #cmdPrint.write(row['category'] + '\n')     # Debug print to console
                                if row['category'] not in ps.categoryList or row['category'] == '<< Uncategorised >>':
                                    window[f'-TransGrid_{i}_3_0-'].Update(row['category'], font='Any 10 bold')     # If Pocketsmith had assigned a category different to our own or not categorised, then show it in bold face to differentiate from others
                                else:
                                    window[f'-TransGrid_{i}_3_0-'].Update(row['category'], font='Any 10')
                            except Exception as ex:
                                # Generic exception reporting (to find out where the error occurred). Ref: https://stackoverflow.com/a/9824050/7251433
                                cmdPrint.write(f'An exception of type {type(ex).__name__} occurred. Arguments:\n{ex.args}')
                            window[f'-TransGrid_{i}_4_0-'].Update(row['payee'])
                            window[f'-TransGrid_{i}_6_0-'].Update(row['note'])

        if '-TransGrid_' in event:          # Amount change event. Only for Amount field event change is activated. Event may be like this:  -TransGrid_x_2_n-     where x is row number and n=0..4
            row = int(event.split('_')[1])  # Get row number
            # Split's remaining amount rationality check. Sum the amounts in main and split transactions, and show difference in split remaining amount
            #if f'-TransGrid_{row}_2' in event:   # Amount change event
            #cmdPrint.write(event + '\n')
            amtSum = 0.0
            for i in range(0, panel.splitRowsCount):
                try:
                    amt = float(window[f'-TransGrid_{row}_2_{i}-'].get().replace(',',''))       # Removing , separator before float conversion
                    amtSum += amt
                    # Colour the entered amount. Note: Code commented out as it prevent arrow keys to move cursor in the Input field. Check for another method to implement colour coding the amount
                    # if amt > 0.001:
                    #     window[f'-TransGrid_{row}_2_{i}-'].Update(window[f'-TransGrid_{row}_2_{i}-'].get(), text_color='green')
                    # elif amt < -0.001:
                    #     window[f'-TransGrid_{row}_2_{i}-'].Update(window[f'-TransGrid_{row}_2_{i}-'].get(), text_color='brown')
                    # else:
                    #     window[f'-TransGrid_{row}_2_{i}-'].Update(window[f'-TransGrid_{row}_2_{i}-'].get(), text_color='black')
                except:
                    pass        # Amount on field on split row may be empty an string - ignore them
            # Update split remaining amount indicator
            diff = (unconfirmedTransactionAmount[row]-amtSum)
            if diff < -0.001:
                window[f'-SplitRowRemAmt_{row}_1-'].Update('%.2f' % diff, text_color='red', font='Any 10 bold')
            elif diff > 0.001:
                window[f'-SplitRowRemAmt_{row}_1-'].Update('%.2f' % diff, text_color='green', font='Any 10 bold')
            elif diff < 0.0:        # Just to remove minus sign from remaining very small negative amounts eg. -0.000000001
                window[f'-SplitRowRemAmt_{row}_1-'].Update('%.2f' % (diff*-1), text_color='black', font='Any 10 bold')
            else:
                window[f'-SplitRowRemAmt_{row}_1-'].Update('%.2f' % diff, text_color='black', font='Any 10 bold')


        if '-TransGridApprove' in event:
            # Rationality checks:
            #   1. Check split Remaining amount is zero. Don't approve if this condition isn't met
            #   2. For each transaction, check date, account, amount and category are valid, to post that transaction. Other fields are optional
            #   3. If Transfer To account is given and valid, make a double entry with inverse amount. Change Payee to "Transfer : xxx" for both double transactions, where xxx is name of each other's account name
            #   4. If all posts to server are successful, hide the transaction rows
            cmdPrint.write('Debug 3' + '\n')
            row = int(event.split('_')[1])
            try:
                remAmt = float(window[f'-SplitRowRemAmt_{row}_1-'].get())
            except:
                remAmt = 0.0
            if ut.IsFloatValueZero(remAmt):
                cmdPrint.write('Debug 3b' + '\n')
                # Check user input data are valid
                valid = [False for i in range(0, panel.splitRowsCount)]
                resp = ['' for i in range(0, panel.splitRowsCount)]
                for i in range(0, panel.splitRowsCount):
                    valid[i], resp[i] = ValidateFields(window[f'-TransGrid_{row}_0_{i}-'].get(),    # Date
                                                       window[f'-TransGrid_{row}_1_{i}-'].get(),    # Account name
                                                       window[f'-TransGrid_{row}_2_{i}-'].get(),    # Amount
                                                       window[f'-TransGrid_{row}_3_{i}-'].get(),    # Category
                                                       window[f'-TransGrid_{row}_5_{i}-'].get())    # Transfer account name
                if False in valid:
                    # Some input data is invalid. When there's no error, we expect all elements to be True in valid[] list
                    errorMsgIdx = valid.index(False)
                    window['-ReviewTab_Status-'].Update(' ' * 70 + resp[errorMsgIdx], text_color='red', font='Any 12 bold')
                    cmdPrint.write('Debug 3c' + '\n')
                else:
                    window['-ReviewTab_Status-'].Update('', text_color='black')     # Clear status message
                    # Input data are valid. Post transactions to Pocketsmith
                    status = ''
                    cmdPrint.write('Debug 3d-1' + '\n')
                    for i in range(0, panel.splitRowsCount):        # For each Approve request, loop through main transaction and splits
                        transDict = {}
                        res1 = ''
                        if resp[i] == 'No transfer':
                            cmdPrint.write(f"Debug 3d-2: {unconfirmedTransactions[row]['date']}" + '\n')
                            # Main transaction should be updated, split transactions should be created as new
                            if i == 0:
                                # Main transaction
                                transDict[panel.TRANSACTION_DATE] = unconfirmedTransactions[row]['date']
                                cmdPrint.write(f"Debug 3d-3: {unconfirmedTransactions[row]['account']}" + '\n')
                                transDict[panel.AC_FROM] = unconfirmedTransactions[row]['account']
                                cmdPrint.write('Debug 3e' + '\n')
                                transDict[panel.AMOUNT]           = window[f'-TransGrid_{row}_2_{i}-'].get()
                                transDict[panel.CATEGORY_NAME]    = window[f'-TransGrid_{row}_3_{i}-'].get()
                                transDict[panel.PAYEE_NAME]       = window[f'-TransGrid_{row}_4_{i}-'].get()
                                transDict[panel.AC_TO]            = window[f'-TransGrid_{row}_5_{i}-'].get()
                                cmdPrint.write('Debug 3f' + '\n')
                                transDict[panel.NOTE_TEXT]        = window[f'-TransGrid_{row}_6_{i}-'].get()
                                #cmdPrint.write('-----------------------------------------------' + '\n')
                                #cmdPrint.write(str(transDict) + '\n')
                                cmdPrint.write('Debug 3g' + '\n')
                                res1, res2, status = ps.UpdateTransaction(unconfirmedTransactions[row]['id'], transDict, Need_Review=False)
                                # cmdPrint.write('Res1: ' + '\n')
                                # cmdPrint.write(str(res1) + '\n')
                                # cmdPrint.write('Res2: ' + '\n')
                                # cmdPrint.write(str(res2) + '\n')
                                cmdPrint.write('Debug 3h' + '\n')
                            else:
                                cmdPrint.write('Debug 3-2a' + '\n')
                                transDict[panel.TRANSACTION_DATE] = unconfirmedTransactions[row]['date']
                                transDict[panel.AC_FROM]          = unconfirmedTransactions[row]['account']
                                transDict[panel.AMOUNT]           = window[f'-TransGrid_{row}_2_{i}-'].get()
                                transDict[panel.CATEGORY_NAME]    = window[f'-TransGrid_{row}_3_{i}-'].get()
                                transDict[panel.PAYEE_NAME]       = unconfirmedTransactions[row]['payee']         # We create new split transaction with 'original_payee' of main trans. This may help with correct clearing of pending transaction. Pocketsmith may use 'original_payee' to group sum to match bank amount. Not sure about this as we haven't verified otherwise
                                transDict[panel.AC_TO]            = window[f'-TransGrid_{row}_5_{i}-'].get()
                                transDict[panel.NOTE_TEXT]        = window[f'-TransGrid_{row}_6_{i}-'].get()
                                cmdPrint.write('Debug 3-2b' + '\n')
                                res1, res2, status = ps.PostTransaction(transDict, Need_Review=False)
                                cmdPrint.write('Debug 3-2c' + '\n')
                                if 'SUCCESS' in status.upper():     # When we create new transaction, we need to run an Update Transaction API to clear the review flag in Pocketsmith. Even with needs_review flag is set to False, a newly created transaction always comes up for review
                                    transDict[panel.PAYEE_NAME] = window[f'-TransGrid_{row}_4_{i}-'].get()        # Get new payee name from input field
                                    cmdPrint.write('Debug 3-2d' + '\n')
                                    res1, res2, status = ps.UpdateTransaction(res1['id'], transDict, Need_Review=False) # Using id of the newly created transaction in the above step, to update it
                                    cmdPrint.write('Debug 3-2e' + '\n')
                                    # cmdPrint.write(str(res1) + '\n')
                                    # cmdPrint.write('-----------------------------------------------' + '\n')
                                    # cmdPrint.write(status + '\n')
                                    # cmdPrint.write('-----------------------------------------------' + '\n')

                        elif resp[i] == 'Transfer':
                            # Main transaction should be updated, split transactions should be created as new
                            transDict = {}
                            if i == 0:
                                # Main transaction
                                cmdPrint.write('Debug 3-3a' + '\n')
                                transDict[panel.TRANSACTION_DATE] = unconfirmedTransactions[row]['date']
                                transDict[panel.AC_FROM]          = unconfirmedTransactions[row]['account']
                                cmdPrint.write('Debug 3-3b' + '\n')
                                transDict[panel.AMOUNT]           = window[f'-TransGrid_{row}_2_{i}-'].get()
                                transDict[panel.CATEGORY_NAME]    = window[f'-TransGrid_{row}_3_{i}-'].get()
                                transDict[panel.PAYEE_NAME]       = window[f'-TransGrid_{row}_4_{i}-'].get()
                                transDict[panel.AC_TO]            = window[f'-TransGrid_{row}_5_{i}-'].get()
                                transDict[panel.NOTE_TEXT]        = window[f'-TransGrid_{row}_6_{i}-'].get()
                                res1, res2, status = ps.UpdateTransaction(unconfirmedTransactions[row]['id'], transDict, Need_Review=False)
                                # cmdPrint.write('Res1: ' + '\n')
                                # cmdPrint.write(str(res1) + '\n')
                                # cmdPrint.write('Res2: ' + '\n')
                                # cmdPrint.write(str(res2) + '\n')
                                cmdPrint.write('Debug 3-3c' + '\n')
                                res1, status = ps.ConfirmTransaction(unconfirmedTransactions[row]['id'])
                                cmdPrint.write('Debug 3-3d' + '\n')

                            else:
                                transDict[panel.TRANSACTION_DATE] = unconfirmedTransactions[row]['date']
                                transDict[panel.AC_FROM]          = unconfirmedTransactions[row]['account']
                                cmdPrint.write('Debug 3-4a' + '\n')
                                transDict[panel.AMOUNT]           = window[f'-TransGrid_{row}_2_{i}-'].get()
                                transDict[panel.CATEGORY_NAME]    = window[f'-TransGrid_{row}_3_{i}-'].get()
                                transDict[panel.PAYEE_NAME]       = unconfirmedTransactions[row]['payee']         # We create new split transaction with 'original_payee' name of main trans. This may help with correct clearing of pending transaction. Pocketsmith may use 'original_payee' to group sum to match bank amount. Not sure about this as we haven't verified otherwise
                                transDict[panel.AC_TO]            = window[f'-TransGrid_{row}_5_{i}-'].get()
                                transDict[panel.NOTE_TEXT]        = window[f'-TransGrid_{row}_6_{i}-'].get()
                                cmdPrint.write('Debug 3-4b' + '\n')
                                res1, res2, status = ps.PostTransaction(transDict, Need_Review=False, ChangePayeeName=False)        # For split transfer transaction, Payee name is not changed in the first creation of transaction as we want to clone payee of original
                                cmdPrint.write('Debug 3-4c' + '\n')
                                if 'SUCCESS' in status.upper():     # When we create new transaction, we need to run an Update Transaction API to clear the review flag in Pocketsmith. Even with needs_review flag is set to False, a newly created transaction always comes up for review
                                    cmdPrint.write('Debug 3-4d' + '\n')
                                    res1, res2, status = ps.UpdateSplitTranferTransactions(res1['id'], res2['id'], transDict)
                                    cmdPrint.write('Debug 3-4e' + '\n')

                        else:   # Ignore split rows without any amount input
                            pass

                        if 'FAILED' in status.upper():
                            cmdPrint.write('Debug 3i: API error: ' + status + '\n')
                            window['-ReviewTab_Status-'].Update(' ' * 5 + status, text_color='red', font='Any 12')
                            break
                        else:
                            # Success. Transaction approval process for requested row (either main or split) is successful.
                            # It was noted that sometimes the main transaction repeatedly appear for confirmation even after it was confirmed before.
                            #  Usually, happens with bank synced trans while they remain on Pending state. It can also happen when main trans amount is split.
                            #  To prevent such confirmation repetitions, we can save approved main transactions of the last 10 or 15 days with their IDs and when they come up again, the script can detect and automatically clear them again.
                            if i == 0:      # We need to save only the main transactions, not splits
                                cmdPrint.write('\nApproved main transaction details:' + '\n')
                                if isinstance(res1, dict):
                                    transDict[panel.PAYEE_NAME] = res1['payee']  # res1 is a response data from API call. We get the payee from res1 in case the payee name was changed to 'Transfer : xxx'
                                else:
                                    pass    # Should not get here, since trans update is already successful, so res1 should be valid dictionary
                                x = f"  --> {unconfirmedTransactions[row]['id']} | {transDict[panel.TRANSACTION_DATE]} | {transDict[panel.AC_FROM]} | {transDict[panel.AMOUNT]} | {transDict[panel.PAYEE_NAME]} | {transDict[panel.NOTE_TEXT]}"
                                cmdPrint.write(x + '\n\n')
                                # Save approved main transaction to file using transaction id as key. Using stored data, we can later look up and auto clear it if the transaction comes up again for approval
                                transDict.pop(panel.AC_TO)      # Discard unwanted AccountTo data from dict. We won't need AccountTo info to reconfirm re-appearing transactions for repeated confirmation
                                approvedTransactionDict[unconfirmedTransactions[row]['id']] = transDict
                                ps.SaveApprovedTransaction(approvedTransactionDict)
                                #cmdPrint.write('\nAPI response details:' + '\n')
                                #cmdPrint.write('  --> ' + str(res1) + '\n')

                    if 'SUCCESS' in status.upper():
                        window['-ReviewTab_Status-'].Update(' ' * 50 + status, text_color='green', font='Any 12')
                        # Hide the cleared transaction and any splits
                        window[event].hide_row()  # Hide the row where the button was pressed
                        unconfirmedTransactionApproved[row] = True
                        for i in range(1, panel.splitRowsCount):  # Hide all of the sub split rows belonging to the main transaction
                            window[f'-SplitRow_{row}_{i}-'].hide_row()
                        window[f'-TransGrid_SpacerRow_{row}-'].hide_row()  # Hide spacer row
                        hiddenSplitRow[row] = 0  # Clear tracking counter for split transaction rows
                        cmdPrint.write('Debug 3j - Requested approval successfully completed' + '\n')

            else:
                window['-ReviewTab_Status-'].Update(' ' * 50 + 'Amount total including any splits, does not match amount Pocketsmith! Adjust amounts and try again.', text_color='red', font='Any 12 bold')

            # If all unconfirmed transactions are approved, clear header and display a message
            if False not in unconfirmedTransactionApproved:
                cmdPrint.write('Debug 3k' + '\n')
                window['-TransGridHeadingRow-'].hide_row()
                window['-ReviewTab_Status-'].Update(' ' * 95 + 'All cleared. Well done!', text_color='green', font='Any 14 bold')
                cmdPrint.write('Debug 3L - All approvals complete' + '\n')


        if '-TransGridSplit' in event:
            # To insert rows for split transactions, first hide all subsequent rows
            row = int(event.split('_')[1])
            if hiddenSplitRow[row] < (panel.splitRowsCount - 1):          # Check if we have already reached maximum number of allowed splits. If panel.splitRowsCount is 5, then split rows are 1,2,3,4
                window[f'-TransGrid_SpacerRow_{row}-'].hide_row()       # First hide any existing spacer row that may be after last split transaction
                for r in range(row+1, len(unconfirmedTransactions)):
                    window[f'-TransGridApprove_{r}_0-'].hide_row()       # Hide all subsequent transaction rows
                    for i in range(1, panel.splitRowsCount):              # Hide splits of next main transactions too
                        window[f'-SplitRow_{r}_{i}-'].hide_row()
                    window[f'-TransGrid_SpacerRow_{r}-'].hide_row()

                # Unhide one split row of the requested main transactions
                window[f'-SplitRow_{row}_{hiddenSplitRow[row]+1}-'].unhide_row()
                # Copy required transaction details (date, account name and payee) into split transaction fields
                window[f'-TransGrid_{row}_0_{hiddenSplitRow[row]+1}-'].Update(window[f'-TransGrid_{row}_0_0-'].get())       # Date
                window[f'-TransGrid_{row}_1_{hiddenSplitRow[row]+1}-'].Update(window[f'-TransGrid_{row}_1_0-'].get())       # Account name
                window[f'-TransGrid_{row}_4_{hiddenSplitRow[row]+1}-'].Update(window[f'-TransGrid_{row}_4_0-'].get())       # Payee
                # Unhide spacer row
                window[f'-TransGrid_SpacerRow_{row}-'].unhide_row()
                hiddenSplitRow[row] += 1
                if hiddenSplitRow[row] > 1:
                    # We only need remaining amount tracking on first split row. Clear on others
                    window[f'-SplitRowRemAmtTitle_{row}_{hiddenSplitRow[row]}-'].Update('')
                    window[f'-SplitRowRemAmt_{row}_{hiddenSplitRow[row]}-'].Update('')


                # If main unconfirmed transaction is not already Approved, then bring back original transactions that were temporarily hidden to insert above split row.
                #   We do it this way because, when we unhide a hidden row, PysimpleGui always add to the bottom of the visible rows
                for r in range(row+1, len(unconfirmedTransactions)):
                    if unconfirmedTransactionApproved[r] == False:
                        window[f'-TransGridApprove_{r}_0-'].unhide_row()
                        i = 1
                        while i <= hiddenSplitRow[r]:           # Also re-instate any split transaction rows for each unapproved main transaction
                            window[f'-SplitRow_{r}_{i}-'].unhide_row()
                            i += 1
                        if i > 1:
                            window[f'-TransGrid_SpacerRow_{r}-'].unhide_row()

        if '-TransGridReject' in event:
            pass        # Note: Functionality for Reject button is not implemented. Reject button from GUI panel may be removed if not required.

        # If any window element values changed, backup the values
        if values != fieldValuesCurrent:  # We against saved Master double copy and only update json when there's a difference.  Comparing two dictionaries  Ref: https://stackoverflow.com/a/40921229
            if values['-Payee_Name-'] == '':
                # Debug print to trap when field values goes missing from json
                cmdPrint.write('Field values:' + '\n')
                cmdPrint.write(str(fieldValuesCurrent) + '\n')
                cmdPrint.write('\nNew values:' + '\n')
                cmdPrint.write(str(values) + '\n')

            fieldValuesCurrent = values   # We do this double backup of values, because when clicking the X button to close the window will yield a None in 'values'. Later when writing to json, we use fieldValuesCurrent, which will have valid data


    # Closing the GUI window after Exit button or window X is clicked
    window.close()

    # Restore original stdout, stderr object pointer
    sys.stdout = cmdPrint
    sys.stderr = cmdErr

    # Save the window element values to json file, if values changed from last saved data
    if fieldValuesCurrent != panel.fieldValues:
        panel.saveFieldValues(fieldValuesCurrent)


# Function to display No Review message when there are no outstanding transactions to review
def NoReviewCheck(UnconfirmedTransactions, WindowObj):
    if len(UnconfirmedTransactions) == 0:
        event, values = WindowObj.read(timeout=50)  # Dummy read() to enable Update() work to work
        WindowObj['-ReviewTab_Status-'].Update(' ' * 90 + 'No new transactions to review', text_color='darkblue', font='Any 12 bold')  # Using Update() to update the value of the InputText box.  Ref: https://pysimplegui.readthedocs.io/en/latest/call%20reference/#window/#Update
        WindowObj['-TransGridHeadingRow-'].hide_row()

# Function to validate required transaction input data. Ref: https://stackoverflow.com/a/16870699
# Pocksmith accepts any of the 4 different date formats checked here. Todo improve format check using regex
def ValidateFields(DateStr, AccountName, Amount, Category, AccountToName):
    if Amount == '':          # If there's no amount, then we don't data in other fields
        return True, 'Ignore'

    # Check date format
    if not ut.IsDateFormatValid(DateStr)[0]:
        return False, 'Invalid date!'

    # Account check
    if AccountName not in ps.accountList:
        return False, 'Invalid account name!'

    # Category check
    if Category not in ps.categoryList:
        return False, 'Invalid category!'

    # Transfer To account check
    if (AccountToName not in ps.accountList and AccountToName != '') or (AccountName == AccountToName):
        return False, 'Invalid transfer account name!'      # Either AccountTo name is invalid or both AccountFrom and AccountTo are same. Both cases are invalid

    if AccountToName == '':
        return True, 'No transfer'
    else:
        return True, 'Transfer'

if __name__ == "__main__":
    if len(sys.argv) == 1:
        main()                      # If no program parameters (eg. python <this file>), start main GUI panel
    else:
        ps.GetUserTransactions()    # If called with additional parameter, run in console. Used for testing & debugging
