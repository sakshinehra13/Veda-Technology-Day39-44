import json
import os
from datetime import datetime
import streamlit as st
import pandas as pd

# File storage
DATA_FILE = "expenses_data.json"

def load_data():
    """Load expenses and budgets from JSON storage."""
    if not os.path.exists(DATA_FILE):
        return {"expenses": [], "budgets": {}}
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return {"expenses": [], "budgets": {}}

def save_data(data):
    """Save expenses and budgets to JSON storage."""
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Page Configuration
st.set_page_config(page_title="Expense & Budget Tracker", page_icon="💳", layout="wide")

# Load session data
data = load_data()

st.title("💳 Personal Expense & Budget Tracker")
st.markdown("A clean, interactive dashboard to manage your daily expenses, monitor categories, and track monthly budgets.")

# Sidebar Navigation
st.sidebar.header("Navigation")
menu = ["Dashboard & Summary", "Add Expense", "Manage Expenses", "Set Monthly Budget", "Search & Filter"]
choice = st.sidebar.selectbox("Choose Action", menu)

# ----------------- 1. DASHBOARD & SUMMARY -----------------
if choice == "Dashboard & Summary":
    st.subheader("📊 Spending Dashboard & Summaries")
    
    if not data["expenses"]:
        st.info("No expense records found yet. Go to 'Add Expense' to get started!")
    else:
        df = pd.DataFrame(data["expenses"])
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime('%Y-%m')
        
        # Metrics overview
        total_spent = df['amount'].sum()
        current_month = datetime.today().strftime('%Y-%m')
        current_month_spent = df[df['month'] == current_month]['amount'].sum()
        current_budget = data["budgets"].get(current_month, 0.0)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Overall Spent", f"${total_spent:,.2f}")
        col2.metric(f"Spent This Month ({current_month})", f"${current_month_spent:,.2f}")
        col3.metric(f"Budget This Month", f"${current_budget:,.2f}" if current_budget > 0 else "Not Set")
        
        # Budget Alert Banner
        if current_budget > 0 and current_month_spent > current_budget:
            st.error(f"⚠️ Budget Alert: You have exceeded your budget for {current_month} by ${current_month_spent - current_budget:,.2f}!")
        elif current_budget > 0:
            st.success(f"✅ You are within your budget for {current_month} (${current_budget - current_month_spent:,.2f} remaining).")

        st.divider()

        # Visualizations & Totals
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("### 📂 Category-wise Spending")
            cat_df = df.groupby("category")["amount"].sum().reset_index()
            st.dataframe(cat_df, use_container_width=True)
            st.bar_chart(cat_df.set_index("category"))

        with col_b:
            st.markdown("### 📅 Monthly Spending Trends")
            monthly_df = df.groupby("month")["amount"].sum().reset_index()
            st.dataframe(monthly_df, use_container_width=True)
            st.line_chart(monthly_df.set_index("month"))

# ----------------- 2. ADD EXPENSE -----------------
elif choice == "Add Expense":
    st.subheader("➕ Add a New Expense")
    
    with st.form("expense_form"):
        amount = st.number_input("Amount ($)", min_value=0.01, format="%.2f", step=1.0)
        date = st.date_input("Transaction Date", value=datetime.today())
        category = st.selectbox("Category", ["Food", "Travel", "Utilities", "Entertainment", "Shopping", "Health", "Other"])
        description = st.text_input("Description / Notes (Optional)")
        
        submit = st.form_submit_button("Save Expense")
        
        if submit:
            new_expense = {
                "id": len(data["expenses"]) + 1 if not data["expenses"] else data["expenses"][-1]["id"] + 1,
                "amount": amount,
                "date": date.strftime("%Y-%m-%d"),
                "category": category,
                "description": description
            }
            data["expenses"].append(new_expense)
            save_data(data)
            st.success("🎉 Expense added successfully!")

# ----------------- 3. MANAGE EXPENSES (VIEW / EDIT / DELETE) -----------------
elif choice == "Manage Expenses":
    st.subheader("✏️ View, Edit, or Delete Expenses")
    
    if not data["expenses"]:
        st.info("No records available to manage.")
    else:
        df = pd.DataFrame(data["expenses"])
        st.dataframe(df, use_container_width=True)
        
        st.divider()
        st.markdown("### Delete an Expense")
        expense_ids = [exp["id"] for exp in data["expenses"]]
        del_id = st.selectbox("Select Expense ID to Delete", expense_ids)
        
        if st.button("Delete Selected Expense", type="primary"):
            data["expenses"] = [exp for exp in data["expenses"] if exp["id"] != del_id]
            save_data(data)
            st.success(f"Successfully deleted expense ID {del_id}!")
            st.rerun()

# ----------------- 4. SET MONTHLY BUDGET -----------------
elif choice == "Set Monthly Budget":
    st.subheader("🎯 Set or Update Monthly Budget")
    
    with st.form("budget_form"):
        default_month = datetime.today().strftime("%Y-%m")
        month_input = st.text_input("Enter Month (YYYY-MM)", value=default_month)
        budget_amount = st.number_input("Budget Limit ($)", min_value=0.0, format="%.2f", step=50.0)
        
        save_budget = st.form_submit_button("Set Budget")
        
        if save_budget:
            data["budgets"][month_input] = budget_amount
            save_data(data)
            st.success(f"🎯 Budget for {month_input} successfully set to ${budget_amount:,.2f}!")

# ----------------- 5. SEARCH & FILTER -----------------
elif choice == "Search & Filter":
    st.subheader("🔍 Search and Filter Records")
    
    if not data["expenses"]:
        st.info("No data available for searching.")
    else:
        filter_type = st.radio("Filter By:", ["Category", "Month (YYYY-MM)"])
        df = pd.DataFrame(data["expenses"])
        
        if filter_type == "Category":
            selected_cat = st.selectbox("Select Category", df["category"].unique())
            filtered_df = df[df["category"] == selected_cat]
        else:
            df['month'] = pd.to_datetime(df['date']).dt.strftime('%Y-%m')
            selected_month = st.selectbox("Select Month", df["month"].unique())
            filtered_df = df[df['month'] == selected_month]
            
        st.markdown(f"### Results ({len(filtered_df)} found)")
        st.dataframe(filtered_df, use_container_width=True)