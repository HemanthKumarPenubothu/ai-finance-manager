
import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px

CURRENCY = "₹"

# ---  CORE LOGIC (No changes here) ---
def get_data_filename():
    """Generates a filename for the current month, e.g., 'transactions_2025-08.csv'."""
    current_month = datetime.now().strftime('%Y-%m')
    return f"transactions_{current_month}.csv"

def load_transactions(filename):
    """Loads transactions from a given CSV file."""
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        return pd.read_csv(filename)
    else:return pd.DataFrame(columns=['type', 'category', 'amount', 'date'])

def save_transactions(df, filename):
    """Saves the DataFrame to the given CSV file, ensuring consistent column order."""
    df_to_save = df[['type', 'category', 'amount', 'date']]
    df_to_save.to_csv(filename, index=False)
    st.success(f"Data saved to {filename}!")


# --- STREAMLIT UI ---
st.set_page_config(page_title="AI Finance Manager", page_icon="💰", layout="wide")

if 'transactions_df' not in st.session_state:
    st.session_state.transactions_df = load_transactions(get_data_filename())

st.title("💰 AI-Powered Personal Finance Manager")
st.write(f"You are managing transactions for: `{get_data_filename()}`")


# ---  SIDEBAR ACTIONS (We add the budget feature here) ---
st.sidebar.header("Actions")

# --- Budget Setting Form ---
st.sidebar.header("Set Your Budget")
with st.sidebar.form(key="budget_form"):
    monthly_budget = st.number_input(f"Enter Your Monthly Budget ({CURRENCY})", min_value=0.0, step=1000.0)
    submit_budget = st.form_submit_button("Set Budget")
    if submit_budget:
        st.session_state.monthly_budget = monthly_budget
        st.sidebar.success(f"Monthly budget set to {CURRENCY}{monthly_budget:,.2f}")


if 'monthly_budget' in st.session_state:
     st.sidebar.metric(label="Your Monthly Budget", value=f"{CURRENCY}{st.session_state.monthly_budget:,.2f}")


st.sidebar.header("Add New Transaction")
with st.sidebar.form(key="add_transaction_form", clear_on_submit=True):
    trans_type = st.selectbox("Type", ["expense", "income"])
    trans_category = st.text_input("Category (e.g., Groceries, Salary)")
    trans_amount = st.number_input("Amount", min_value=0.0, format="%.2f")
    trans_date = st.date_input("Date", datetime.now())
    submit_button = st.form_submit_button(label="Add Transaction")

    if submit_button:
        if not trans_category:
             st.sidebar.error("Please enter a category.")
        else:
            new_transaction = pd.DataFrame([{'type': trans_type, 'category': trans_category, 'amount': trans_amount, 'date': trans_date.strftime('%Y-%m-%d')}])
            st.session_state.transactions_df = pd.concat([st.session_state.transactions_df, new_transaction], ignore_index=True)
            save_transactions(st.session_state.transactions_df, get_data_filename())
            st.sidebar.success("Transaction added!")
            st.rerun()

st.sidebar.header("Upload CSV")
uploaded_file = st.sidebar.file_uploader("Upload your transaction CSV", type="csv")
if uploaded_file is not None:
    uploaded_df = pd.read_csv(uploaded_file)
    expected_columns = {'type', 'category', 'amount', 'date'}
    if expected_columns.issubset(set(uploaded_df.columns)):
        st.session_state.transactions_df = pd.concat([st.session_state.transactions_df, uploaded_df], ignore_index=True)
        st.session_state.transactions_df = st.session_state.transactions_df[list(expected_columns)].drop_duplicates(ignore_index=True)
        save_transactions(st.session_state.transactions_df, get_data_filename())
        st.sidebar.success("CSV file uploaded and data merged!")
        st.rerun()
    else:
        st.sidebar.error(f"Upload failed. The CSV is missing required columns.")


# ---  MAIN PAGE DISPLAY ---
st.header("Financial Dashboard")

df = st.session_state.transactions_df
income_df = df[df['type'] == 'income']
expense_df = df[df['type'] == 'expense']
total_income = income_df['amount'].sum()
total_expense = expense_df['amount'].sum()
net_savings = total_income - total_expense

# --- Display Key Metrics (Using the CURRENCY variable) ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"{CURRENCY}{total_income:,.2f}")
col2.metric("Total Expenses", f"{CURRENCY}{total_expense:,.2f}")
col3.metric("Net Savings", f"{CURRENCY}{net_savings:,.2f}")

# --- Budget Progress Bar (need to chsnge the size  )  ---
if 'monthly_budget' in st.session_state and st.session_state.monthly_budget > 0:
    budget = st.session_state.monthly_budget
    st.subheader("Budget Progress")
    progress = total_expense / budget
    # don't forget the CURRENCY variable here
    st.progress(min(progress, 1.0), text=f"{CURRENCY}{total_expense:,.2f} / {CURRENCY}{budget:,.2f} spent")
    if progress > 1:
        st.error("You are over budget!")
    elif progress > 0.85:
        st.warning("You are close to your budget limit!")

st.markdown("---")

# --- VISUALIZATIONS ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("Expenses by Category")
    if not expense_df.empty:
        expense_by_category = expense_df.groupby('category')['amount'].sum().reset_index()
        fig_pie = px.pie(expense_by_category, values='amount', names='category', title="Expense Distribution", color_discrete_sequence=px.colors.sequential.Agsunset)
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("No expense data to display.")
with col2:
    st.subheader("Income vs. Expenses")
    income_expense_data = {'Metric': ['Total Income', 'Total Expenses'], 'Amount': [total_income, total_expense]}
    bar_df = pd.DataFrame(income_expense_data)
    fig_bar = px.bar(bar_df, x='Metric', y='Amount', title="Income and Expense Summary", color='Metric', color_discrete_map={'Total Income':'green', 'Total Expenses':'red'})
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ---  TRANSACTION DATA TABLE AND DELETE FUNCTION (new change test incomplete)---
st.header("Transaction History")

df_display = st.session_state.transactions_df
if not df_display.empty:
    st.dataframe(df_display, use_container_width=True)
    st.subheader("Delete a Transaction")
    if not df_display.empty:
        # dont remove the CURRENCY variable here
        delete_options = [f"{i}: {row['type']} - {row['category']} - {CURRENCY}{row['amount']:.2f}" for i, row in df_display.iterrows()]
        trans_to_delete = st.selectbox("Select transaction to delete", options=delete_options, key="delete_dropdown", index=None, placeholder="Choose a transaction...")
        if st.button("Delete Selected Transaction"):
            if trans_to_delete is not None:
                trans_index_to_delete = int(trans_to_delete.split(':')[0])
                st.session_state.transactions_df = st.session_state.transactions_df.drop(trans_index_to_delete).reset_index(drop=True)
                save_transactions(st.session_state.transactions_df, get_data_filename())
                st.success("Transaction deleted!")
                st.rerun()
            else:
                st.warning("Please select a transaction to delete.")
else:
    st.info("Add a transaction using the sidebar to get started.")