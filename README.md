# PocketSmith
Desktop program to review and approve PocketSmith transactions

To know more about PocketSmith, refer: https://www.pocketsmith.com/

This script was developed with Python 3.7
   - Requires package PySimpleGUI
   - To run script: python PsControl_GUI.py

Prerequisite:
   - You need a developer API key from PocketSmith. Login to your account, goto menu: Setting -> Security & connections and then select Manage developer keys. Create a key and save it in keyFile.json. This file will be created when script is run for the first time.

Transaction Categories:
   - Required custom categories can be created via PocketSmith web interface. However, the PocketSmith can also create new categories when it auto categorise newly bank synced transactions. This script will get all available categories from PocketSmith. If you wish to ignore some of them, create a category 'Hidden Categories' and place it as a last item in the list on PocketSmith web interface. Any new auto categories created after that will not appear in this py tool. If you wish to chnage this behaviour, update LoadCategories() in MyPcocketSmith.py
