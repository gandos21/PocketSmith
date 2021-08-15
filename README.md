# PocketSmith
Desktop program to review and approve PocketSmith transactions


Developed with Python 3.7
   - Requires package PySimpleGUI
   - To run script: python PsControl_GUI.py

Pocketsmith Specifics:
   - Get your developer API key from PocketSmith settings menu (Security & connections -> Manage developer keys), and save it in keyFile.json. This file will be created when script is run for the first time.
   - Required categories can be created in PocketSmith web interface. If a category named 'Hidden' is created, then any categories that appear after 'Hidden' will be ignored by py script. If this behaviour is not desired, update LoadCategories() in MyPcocketSmith.py
