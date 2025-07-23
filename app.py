# Import the pandas library to help us manage our data like a spreadsheet
import pandas as pd
import os # This lets us check if a file exists

# The name of the file where data is saved
TRANSACTIONS_FILE = 'transactions.csv'

def load_all_transactions():
    """
    Checks if our transactions file exists.
    If yes, load it.
    If no, create an empty table for us to use.
    """
    if os.path.exists(TRANSACTIONS_FILE):
        #file is already exists, so read it diretly
        dataframe = pd.read_csv(TRANSACTIONS_FILE)
    else:
        """
        If it is our first time running, so create a new, empty table (DataFrame)
        with the columns we want.
        """
        dataframe = pd.DataFrame(columns=['Date', 'Type', 'Category', 'Amount'])
    
    return dataframe

def save_all_transactions(dataframe):
    # Saves our current data table to the CSV file.
    dataframe.to_csv(TRANSACTIONS_FILE, index=False) # index=False gets rid of an unnecessary column
    print("Your data has been saved.")

def add_new_transaction(dataframe):
    """Guides the user to add a new income or expense item."""
    print("\nLet's add a new transaction.")
    
    # Ask the user for the details
    trans_type = input("transation type : income or an expense? ")
    date = input("Enter the date (e.g.: 1-1-2000): ")
    category = input("What's the category (e.g : Salary, Groceries, Rent)? ")
    amount = float(input("What's the amount? ")) # Use float() to allow deimal values

    # Put the new data into a temporary, one-row table
    new_transaction = pd.DataFrame({
        'Date': [date],
        'Type': [trans_type],
        'Category': [category],
        'Amount': [amount]
    })
    
    # Append our new transaction to the main data table
    updated_dataframe = pd.concat([dataframe, new_transaction], ignore_index=True)
    print("Transaction is successfully added!")
    return updated_dataframe

def show_all_transactions(dataframe):
    # Prints out all the recorded transactions till date.
    print("\n--- Here Are All Your Transactions ---")
    
    if dataframe.empty:
        print("You haven't added any transactions yet.")
    else:
        # If we have data, print the whole table
        print(dataframe.to_string()) # .to_string() to look look good 
        
    print("--------------------------------------\n")

# ===============================================================
# start of mainn page code ,note: fix code on line 74 loop lo error
# ===============================================================

# loa existing transactions to the file
my_transactions = load_all_transactions()

# running till i exit the loop
while True:
    # menu
    print("\nWelcome to Your Personal Finance Manager!")
    print("What would you like to do?")
    print("  1. Add a new transaction")
    print("  2. See all transactions")
    print("  3. Save and quit the program")
    
    # i/p of user
    user_choice = input("Please enter a number (1, 2, or 3): ")

    if user_choice == '1':
        # function call to add a new transaction
        my_transactions = add_new_transaction(my_transactions)
        
    elif user_choice == '2':
        # function to display everything
        show_all_transactions(my_transactions)
        
    elif user_choice == '3':
        # function to save the data and then break the loop
        save_all_transactions(my_transactions)
        print("Goodbye!")
        break # don't remove or loop runs for ever
        
    else:
        # wrong choice
        print("Sorry, that's not a valid option. Please try again.")