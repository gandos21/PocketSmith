# Window layout setup
#  Created using PySimepleGUI package. Template from window panel was taken from https://pysimplegui.readthedocs.io/en/latest/cookbook/
#  G Yoga - gyalias@yogarajah.net
import PySimpleGUI as sg
from datetime import date
import json

# Constants & configs
NUM_ROWS_FOR_SPLIT      = 5     # Num of rows required to enter split transactions, including a row for main transaction. eg. 5 means, 1 + 4 splits possible
panelDefaultsFileName   = 'PanelDefaults.json'
logoFileName            = 'logo.png'


# Class of data fields used on window panels
class WindowFields:
    # Panel field's key names
    #  Macros style attributes used for field keys for better readability.
    #  Prefixing and suffixing with '-' for GUI element keys is a convention followed in PySimpleGUI. Ref: https://pysimplegui.readthedocs.io/en/latest/#keys
    TRANSACTION_DATE    = '-Transaction_Date-'
    PAYEE_NAME          = '-Payee_Name-'
    CATEGORY_NAME       = '-Category_Name-'
    NOTE_TEXT           = '-Note_Text-'
    AMOUNT              = '-Amount-'
    AC_FROM             = '-Account_From-'
    AC_TO               = '-Account_To-'
    AC_TRANSFER         = '-Account_Transfer-'
    TRANSACTION_ID      = '-Transaction_Id-'

    # Panel field value defaults
    fieldValues = {
        TRANSACTION_DATE    : '',
        PAYEE_NAME          : '',
        CATEGORY_NAME       : '',
        NOTE_TEXT           : '',
        AMOUNT              : 0.00,
        AC_FROM             : '',
        AC_TO               : '',
        AC_TRANSFER         : True,
        TRANSACTION_ID      : ''
    }

    def __init__(self):
        pass

# Layout class
class WindowLayout(WindowFields):       # Inherit Window Field names
    def __init__(self, accountList, categoryList, unconfirmedTransactions, fieldValues=None):
        super().__init__()
        self.accountList = accountList
        self.categoryList = categoryList
        self.unconfirmedTransactions = unconfirmedTransactions
        self.logoFileName = logoFileName
        self.splitRowsCount = NUM_ROWS_FOR_SPLIT

        if fieldValues is None:
            # Load panel field values from json
            try:   # If file exist load from file, otherwise (file doesn't exist or doesn't contain expected data) create a new json
                with open(panelDefaultsFileName, 'r') as fp:
                    self.fieldValues = json.load(fp)                # Storing and restoring dictionary to/from a json
            except:
                # If json does not exist, create initial version using defaults defined in parent class
                with open(panelDefaultsFileName, 'w') as fp:
                   json.dump(self.fieldValues, fp, indent=4)        # Creating with indentation. Ref: https://stackoverflow.com/a/12309296
        else:
            # Window may be re-initialised with specific panel field values. If value given, use that instead of loading from json or using defaults
            self.fieldValues = fieldValues

    # Layout of window we want to create has 2 tabs: Review and Manual Transaction Entry
    def layout(self):
        transactionEntryTab = self.__transactionEntryTab()
        reviewTab           = self.__reviewTab()

        window_layout = [[sg.TabGroup([[sg.Tab('Review', reviewTab), sg.Tab('Transaction Entry', transactionEntryTab)]], enable_events=True, key='-TabGroup-')] ]
        return window_layout

    # Transaction Entry tab setup
    def __transactionEntryTab(self):
        transactionEntryTab = [
            # Title text and image of Linkt/Viva combined logo
            [sg.Text('Manual Transaction Entry', font='Any 15 bold', pad=(5,(1,1))), sg.Text(55 * ' '), sg.Image(filename=self.logoFileName, pad=(5,(1,1)))],

            # Transaction date
            [sg.Text('Transaction date', size=(17, 1), auto_size_text=False, justification='right'),
             sg.InputText(date.today().strftime("%d-%m-%Y"), size=(15, 1), key=self.TRANSACTION_DATE, enable_events=True)],      # Load today's date in to text field

            # Payee & category
            [sg.Text('Payee', size=(17,1), auto_size_text=False, justification='right'),
             sg.InputText(self.fieldValues[self.PAYEE_NAME], size=(62, 1), key=self.PAYEE_NAME, enable_events=True)],
            [sg.Text('Category', size=(17,1), auto_size_text=False, justification='right'),
             sg.Combo(self.categoryList, size=(60, 1), default_value=self.fieldValues[self.CATEGORY_NAME], key=self.CATEGORY_NAME, enable_events=True)],

            # Horizontal separator line    Ref: https://pysimplegui.readthedocs.io/en/latest/#horizontalseparator-element
            [sg.Text('_' * 90, text_color='grey', pad=(5, (3, 10)))],  # Increased bottom pixel padding from 3 to 10 to give below frames some vertical space  Ref: https://pysimplegui.readthedocs.io/en/latest/#pad

            [sg.Text('Account / Transfer from', size=(17, 1), auto_size_text=False, justification='right'),
             sg.Combo(self.accountList, size=(25,1), default_value=self.fieldValues[self.AC_FROM], key=self.AC_FROM, enable_events=True)],
            [sg.Text('Transfer to (Optional)', size=(17, 1), auto_size_text=False, justification='right'),
             sg.Combo(self.accountList, size=(25, 1), default_value='', key=self.AC_TO, enable_events=True),
             sg.Checkbox('Account Transfer', default=self.fieldValues[self.AC_TRANSFER], key=self.AC_TRANSFER,   enable_events=True)],

            # Horizontal separator line    Ref: https://pysimplegui.readthedocs.io/en/latest/#horizontalseparator-element
            [sg.Text('_' * 90, text_color='grey', pad=(5, (3, 10)))],  # Increased bottom pixel padding from 3 to 10 to give below frames some vertical space  Ref: https://pysimplegui.readthedocs.io/en/latest/#pad

            [sg.Text('Note', size=(17, 1), auto_size_text=False, justification='right'),
             sg.InputText(self.fieldValues[self.NOTE_TEXT], size=(62, 1), key=self.NOTE_TEXT, enable_events=True)],
            [sg.Text('Amount', size=(17, 1), auto_size_text=False, justification='right'),
             sg.InputText(self.fieldValues[self.AMOUNT], size=(15, 1), key=self.AMOUNT, enable_events=True, justification='right')],

            # Horizontal separator line    Ref: https://pysimplegui.readthedocs.io/en/latest/#horizontalseparator-element
            [sg.Text('_'  * 90, text_color='grey', pad=(5,(3,10)))],   # Increased bottom pixel padding from 3 to 10 to give below frames some vertical space  Ref: https://pysimplegui.readthedocs.io/en/latest/#pad

            [sg.Frame('Messages',[
                    [sg.Output(size=(85,10), key='-Output-')]
                ])
            ],
            # Horizontal separator line
            [sg.Text('_'  * 90, text_color='grey', pad=(5,(3,10)))],   # Increased bottom pixel padding from 3 to 10 to give below buttons some vertical space  Ref: https://pysimplegui.readthedocs.io/en/latest/#pad

            [sg.Text('Transaction Id', size=(17, 1), auto_size_text=False, justification='right'),
             sg.InputText(self.fieldValues[self.TRANSACTION_ID], size=(12, 1), key=self.TRANSACTION_ID, enable_events=True)],

            [   # Buttons
                sg.Button('Post',          size=(12,2), font='Any 12', pad=((5, 5), 3)),  # Pixel padding from 5 to 26 to the left of Start button to fit all buttons about the horizontal center of window. Ref: https://pysimplegui.readthedocs.io/en/latest/#pad
                sg.Button('Get Trans', size=(12,2), font='Any 12'),
                sg.Button('Delete Tran', size=(12, 2), font='Any 12'),
                sg.Button('Clear Msg', size=(12,2), font='Any 12'),
                sg.Button('Exit',           size=(12,2), font='Any 12')
            ]
        ]
        return transactionEntryTab

    # Review tab setup
    def __reviewTab(self):
        reviewTabTitle = [[sg.Text('New Transaction Review', font='Any 15 bold'), sg.Button('Refresh', pad=((20, 0), 0), size=(12,1), key='-ReviewDataRefresh-')],
                      [sg.Text('', size=(100, 1), pad=((5, 0), (5, 15)), justification='left', key='-ReviewTab_Status-')]]

        rowHeader = [[sg.Text('Date',        size=(6, 1),  pad=((25, 0), 0),  justification='left', font = 'Any 10 bold', key='-TransGridHeadingRow-'),
                      sg.Text('Account',     size=(8, 1),  pad=((60, 0), 0),  justification='left', font = 'Any 10 bold'),
                      sg.Text('Amount',      size=(8, 1),  pad=((80, 0), 0),  justification='left', font = 'Any 10 bold'),
                      sg.Text('Category',    size=(10, 1), pad=((70, 0), 0),  justification='left', font = 'Any 10 bold'),
                      sg.Text('Payee',       size=(8, 1),  pad=((170, 0), 0), justification='left', font = 'Any 10 bold'),
                      sg.Text('Transfer To', size=(12, 1), pad=((140, 0), 0), justification='left', font = 'Any 10 bold'),
                      sg.Text('Note',        size=(5, 1),  pad=((130, 0), 0), justification='left', font = 'Any 10 bold')]]

        spacerRows = [[sg.Text('', size=(1, 1), pad=(0, 0), font='Any 3', key=f'-TransGrid_SpacerRow_{row}-')]  # An empty row with small font height is used to space out last split row and next main transaction
                      for row in range(len(self.unconfirmedTransactions)) ]

        inputRows = [
                     [sg.Input(              size=(10, 1), pad=((6, 3), (0, 0)), key=f'-TransGrid_{row}_0_{i}-'),    # Date
                      sg.Combo(self.accountList,  size=(22, 1), pad=((3, 3), (0, 0)), key=f'-TransGrid_{row}_1_{i}-'),    # Account
                      sg.Input(              size=(11, 1), pad=((3, 3), (0, 0)), key=f'-TransGrid_{row}_2_{i}-', enable_events=True, justification='right'),       # Amount
                      sg.Combo(self.categoryList,size=(30, 1), pad=((3, 3), (0, 0)), key=f'-TransGrid_{row}_3_{i}-'),    # Category
                      sg.Input(              size=(35, 1), pad=((3, 3), (0, 0)), key=f'-TransGrid_{row}_4_{i}-'),    # Payee
                      sg.Combo(self.accountList,  size=(22, 1), pad=((3, 3), (0, 0)), key=f'-TransGrid_{row}_5_{i}-'),    # Transfer To Account, if double entry to an offline account is required
                      sg.Input(              size=(35, 1), pad=((3, 3), (0, 0)), key=f'-TransGrid_{row}_6_{i}-'),    # Note
                      sg.Button('Approve',   size=(8, 1),  pad=((3, 3), (1, 1)), key=f'-TransGridApprove_{row}_{i}-', button_color=('white', 'green'))   # Approve button
                        if i % self.splitRowsCount == 0 else sg.Text(f'Split {i}', size=(8, 1), pad=((3, 3), (1, 1)), key=f'-SplitRow_{row}_{i}-'),                                   # Button not required on split rows
                      sg.Button('Split',     size=(8, 1), pad=((3, 3), (1, 1)), key=f'-TransGridSplit_{row}_{i}-', button_color=('white', 'darkblue'))   # Split button
                        if i % self.splitRowsCount == 0 else sg.Text('Rem. $', size=(8, 1), pad=((3, 3), (1, 1)), key=f'-SplitRowRemAmtTitle_{row}_{i}-', justification='right', font = 'Any 10 bold'),
                      sg.Button('Reject',    size=(8, 1), pad=((3, 6), (1, 1)), key=f'-TransGridReject_{row}_{i}-', button_color=('white', 'brown'))     # Reject button
                        if i % self.splitRowsCount == 0 else sg.Text('0.00', size=(8, 1), pad=((3, 12), (1, 1)), key=f'-SplitRowRemAmt_{row}_{i}-', font = 'Any 10 bold')
                     ]
                        for row in range(len(self.unconfirmedTransactions)) for i in range(self.splitRowsCount)
                    ]

        reviewTab = reviewTabTitle + rowHeader + spacerRows + inputRows
        return reviewTab

    # Function to save current field values to json
    def saveFieldValues(self, fieldValues):
        with open(panelDefaultsFileName, 'w') as fp:
            json.dump(fieldValues, fp, indent=4)
        print('\t->JSON file updated')
