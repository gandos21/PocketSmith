from datetime import datetime
import re

# Function to convert string formatted date to date type
def StrToDate(DateStr):
    return IsDateFormatValid(DateStr)[1]    # Function IsDateFormatValid() returns tuple of 2 values. We need the second element in the tuple

# Function to check validity of input date string. Input date string may be of four different types checked below
def IsDateFormatValid(DateStr):
    try:
        dt = datetime.strptime(DateStr, '%Y-%m-%d')
    except:
        try:
            dt = datetime.strptime(DateStr, '%d-%m-%Y')
        except:
            try:
                dt = datetime.strptime(DateStr, '%d/%m/%Y')
            except:
                try:
                    dt = datetime.strptime(DateStr, '%Y/%m/%d')
                except:
                    return False, datetime.today()      # Invalid date format
    return True, dt

# Function to check if a given value of type float is near zero
def IsFloatValueZero(floatValue):
    return True if (floatValue < 0.001 and floatValue > -0.001) else False

# Amount separator function. Ref: https://stackoverflow.com/a/13089202
def SepAmount(s, thou=",", dec="."):
    integer, decimal = s.split(".")
    integer = re.sub(r"\B(?=(?:\d{3})+$)", thou, integer)
    return integer + dec + decimal
