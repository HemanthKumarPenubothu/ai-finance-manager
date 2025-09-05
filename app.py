import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import google.generativeai as genai # --- NEW: Import Google's library

# --- Configure Google AI with secret key ---
try:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
except KeyError:
    st.error("Google AI API key not found! Please add it to your .streamlit/secrets.toml file.")
    st.stop()
except Exception as e:
    st.error(f"Error configuring Google AI: {e}")
    st.stop()

# --- All functions ---
CURRENCY = "₹"

def get_data_filename():
    """Generates a filename for the current month."""
    current_month = datetime.now().strftime('%Y-%m')
    return f"transactions_{current_month}.csv"

def load_transactions(filename):
    """Loads transactions from a given CSV file."""
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        return pd.read_csv(filename)
    else:
        return pd.DataFrame(columns=['type', 'category', 'amount', 'date'])

def save_transactions(df, filename):
    """Saves the DataFrame to the given CSV file."""
    df_to_save = df[['type', 'category', 'amount', 'date']]
    df_to_save.to_csv(filename, index=False)
    st.success(f"Data saved to {filename}!")


# --- Switched to Google Gemini ---
def get_ai_savings_tips(expense_df):
    """
    Sends expense data to Google's Gemini Pro model and returns savings tips.
    """
    if expense_df.empty:
        return "Not enough expense data to analyze. Please add more transactions."

    expense_summary = expense_df.groupby('category')['amount'].sum().reset_index()
    prompt_data = "\n".join([f"- {row['category']}: {CURRENCY}{row['amount']:.2f}" for index, row in expense_summary.iterrows()])

    # prompt for the new model
    prompt = f"""
    You are a friendly and helpful financial advisor for a beginner in India.
    Based on the following expense summary in Indian Rupees (INR), provide 3 actionable and simple savings tips.
    Make the tips easy to understand and encouraging. Format the output as a numbered list.

    Expense Summary:
    {prompt_data}
    """
    try:
        # Initialize the Gemini model
        model = genai.GenerativeModel('gemini-pro')
        # This is the new API call
        response = model.generate_content(prompt)
        # Access the response text
        return response.text
    except Exception as e:
        return f"Sorry, I couldn't connect to the Google AI service. Error: {e}"


# --- STREAMLIT UI CODE (The rest of the file is the same) ---
st.set_page_config(page_title="AI Finance Manager", page_icon="💰", layout="wide")

if 'transactions_df' not in st.session_state:
    st.session_state.transactions_df = load_transactions(get_data_filename())

st.title("💰 AI-Powered Personal Finance Manager")
st.write(f"You are managing transactions for: `{get_data_filename()}`")

# Sidebar and other UI elements are unchanged...
st.sidebar.header("Actions")
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


# --- Dashboard display (no changes) ---
st.header("Financial Dashboard")
df = st.session_state.transactions_df
income_df = df[df['type'] == 'income']
expense_df = df[df['type'] == 'expense']
total_income = income_df['amount'].sum()
total_expense = expense_df['amount'].sum()
net_savings = total_income - total_expense

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"{CURRENCY}{total_income:,.2f}")
col2.metric("Total Expenses", f"{CURRENCY}{total_expense:,.2f}")
col3.metric("Net Savings", f"{CURRENCY}{net_savings:,.2f}")

if 'monthly_budget' in st.session_state and st.session_state.monthly_budget > 0:
    budget = st.session_state.monthly_budget
    st.subheader("Budget Progress")
    progress = total_expense / budget
    st.progress(min(progress, 1.0), text=f"{CURRENCY}{total_expense:,.2f} / {CURRENCY}{budget:,.2f} spent")
    if progress > 1: st.error("You are over budget!")
    elif progress > 0.85: st.warning("You are close to your budget limit!")

st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.subheader("Expenses by Category")
    if not expense_df.empty:
        expense_by_category = expense_df.groupby('category')['amount'].sum().reset_index()
        fig_pie = px.pie(expense_by_category, values='amount', names='category', title="Expense Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)
    else: st.info("No expense data to display.")
with col2:
    st.subheader("Income vs. Expenses")
    income_expense_data = {'Metric': ['Total Income', 'Total Expenses'], 'Amount': [total_income, total_expense]}
    bar_df = pd.DataFrame(income_expense_data)
    fig_bar = px.bar(bar_df, x='Metric', y='Amount', title="Income and Expense Summary", color='Metric', color_discrete_map={'Total Income':'green', 'Total Expenses':'red'})
    st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# --- AI FEATURES SECTION ---
st.header("🤖 AI Financial Advisor")

if st.button("Get Basic AI Savings Tips"):
    with st.spinner("Our AI is analyzing your spending..."):
        tips = get_ai_savings_tips(expense_df)
        st.success("Here are your personalized tips!")
        formatted_tips = tips.replace('. ', '.\n\n> ')
        st.markdown(f"> {formatted_tips}")


st.markdown("---")

# --- Transaction History & Delete (no changes) ---
st.header("Transaction History")
if not df.empty:
    st.dataframe(df, use_container_width=True)
    st.subheader("Delete a Transaction")
    delete_options = [f"{i}: {row['type']} - {row['category']} - {CURRENCY}{row['amount']:.2f}" for i, row in df.iterrows()]
    trans_to_delete = st.selectbox("Select transaction to delete", options=delete_options, key="delete_dropdown", index=None, placeholder="Choose a transaction...")
    if st.button("Delete Selected Transaction"):
        if trans_to_delete is not None:
            trans_index = int(trans_to_delete.split(':')[0])
            st.session_state.transactions_df = df.drop(index=trans_index).reset_index(drop=True)
            save_transactions(st.session_state.transactions_df, get_data_filename())
            st.rerun()
else:
    st.info("Add transactions to get started.")