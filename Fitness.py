import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Set background color
st.markdown(
    """
    <style>
    .stApp {
        background-color: #A0A0E8;
    }
    </style>
    """,
    unsafe_allow_html=True
)
 
# Ensure upload directory exists
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load or create leaderboard data
DATA_FILE = "leaderboard.csv"
if os.path.exists(DATA_FILE):
    leaderboard_df = pd.read_csv(DATA_FILE)

    # Ensure Timestamp column is in datetime format
    if not leaderboard_df.empty:
        leaderboard_df["Timestamp"] = pd.to_datetime(leaderboard_df["Timestamp"], errors="coerce")

else:
    leaderboard_df = pd.DataFrame(columns=["Name", "Steps", "Timestamp", "Proof", "Completed"])

    # Define the leaderboard CSV file
DATA_FILE = "leaderboard.csv"

# Load or create leaderboard data
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["Name", "Steps", "Timestamp", "Proof", "Completed", "StepGoalAtSubmission"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

leaderboard_df = load_data()


# Admin authentication setup
ADMIN_CREDENTIALS = {"admin": "securepassword123"}  # Change password for security
admin_username = st.sidebar.text_input("Username", value="", type="password")
admin_password = st.sidebar.text_input("Password", value="", type="password")
is_admin = admin_username in ADMIN_CREDENTIALS and admin_password == ADMIN_CREDENTIALS.get(admin_username)

# Define the step goal file
step_goal_file = "daily_goal.txt"

# Admin logout button
if is_admin:
    if st.sidebar.button("Log Out"):
        st.session_state.pop("admin_username", None)
        st.session_state.pop("admin_password", None)
        st.session_state.pop("is_admin", None)
        st.rerun()

# Admin Panel
if is_admin:
    st.write("### 🛠 Admin Panel: Full CSV Editing")
    
    # Show the current leaderboard as a table
    st.write("#### Current Leaderboard (Click to Edit)")
    edited_df = st.data_editor(leaderboard_df, num_rows="dynamic")  # Enables full editing of the CSV

    # Save button to apply changes
    if st.button("Save Changes"):
        save_data(edited_df)
        st.success("Leaderboard updated successfully!")
        st.rerun()  # Refresh app to update changes

# Allow admin to manually override step goal
if is_admin:
    st.subheader("Override Step Goal")
    manual_step_goal = st.number_input("Set new step goal:", min_value=0, value=0, step=100)

    if st.button("Update Step Goal"):
        if manual_step_goal > 0:
            with open(step_goal_file, "w") as f:
                f.write(str(manual_step_goal))
            st.success(f"Step goal updated to {manual_step_goal}")
            st.rerun()  # Refreshes the app to apply changes


# Streamlit UI
st.image("morphworkslogo4.png", width=650)
st.title("Marchin' Into Spring 2025 Challenge")
st.write("Upload a screenshot of your step count and enter the total steps below.")

#Removed admin panel for setting step goal because step goal is auto set daily
#below this in the code to randomly changing the step challenge goal daily

import random
from datetime import datetime
import os

# Generate a new step goal every day, but allow manual override
today_date = datetime.now().date()
step_goal_file = "daily_goal.txt"

# Read the step goal from file (either auto-generated or manually set)
if os.path.exists(step_goal_file):
    with open(step_goal_file, "r") as f:
        content = f.read().strip()
        step_goal = int(content) if content.isdigit() else None
else:
    step_goal = None

# If no manual step goal is set, generate a random one
if step_goal is None:
    step_goal = int(step_goal) if isinstance(step_goal, str) and step_goal.isdigit() else step_goal


    with open(step_goal_file, "w") as f:
        f.write(str(step_goal))

st.write(f"### 🏆 Today's Step Goal: {step_goal} steps")
#Above this in the code to randomly changing the step challenge goal daily



# User input fields
name = st.selectbox(
    "Select Your Name or Enter a New One:", 
    options=["Enter New Name"] + sorted(leaderboard_df["Name"].astype(str).unique().tolist())
)


if name == "Enter New Name":
    name = st.text_input("Enter your name:")

steps = st.number_input("Enter your steps for today", min_value=1, step=1)
uploaded_file = st.file_uploader("Upload step count screenshot (optional)", type=["jpg", "png", "jpeg"])

# Submit button
if st.button("Submit Steps"):
    if name:
        name = name.strip().lower().title()

        # Save proof image
        proof_filename = None
        if uploaded_file:
            proof_filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            with open(os.path.join(UPLOAD_DIR, proof_filename), "wb") as f:
                f.write(uploaded_file.getbuffer())

        # Check if step goal was met
        completed = steps >= step_goal

        # Record the step entry
        new_entry = pd.DataFrame({
            "Name": [name],
            "Steps": [steps],
            "Timestamp": [datetime.now()],
            "Proof": [proof_filename] if proof_filename else "No Proof",
            "stepgoalatsubmission": [step_goal], #v26 fix (saves step goal at submission)
            "Completed": steps >= step_goal #v26 fix (saves the X and checkmark at submission)
        })
        leaderboard_df = pd.concat([leaderboard_df, new_entry], ignore_index=True)

        # Save to CSV
        leaderboard_df.to_csv(DATA_FILE, index=False)

        st.success(f"Steps recorded for {name}!")
        st.rerun()

# Leaderboard
st.subheader("🏅 Leaderboard")
leaderboard_view = st.selectbox("View Leaderboard:", ["Daily", "Weekly", "Monthly"])

# Ensure Timestamp is in datetime format again before filtering
leaderboard_df["Timestamp"] = pd.to_datetime(leaderboard_df["Timestamp"], errors="coerce")

# Filter leaderboard based on selection
now = datetime.now()
if leaderboard_view == "Daily":
    filtered_df = leaderboard_df[leaderboard_df["Timestamp"].dt.date == now.date()]
    show_completed = True  # Show checkmarks and Xs
else:
    if leaderboard_view == "Weekly":
        filtered_df = leaderboard_df[leaderboard_df["Timestamp"] >= now - pd.Timedelta(days=7)]
    elif leaderboard_view == "Monthly":
        filtered_df = leaderboard_df[leaderboard_df["Timestamp"] >= now - pd.Timedelta(days=30)]
    else:
        filtered_df = leaderboard_df
    show_completed = False  # Hide checkmarks and Xs

# Group by name to sum up steps
filtered_df = filtered_df.groupby("Name", as_index=False).agg({"Steps": "sum"})

# Only show "Completed" column for Daily view
if show_completed:
    filtered_df["Completed"] = filtered_df["Steps"] >= step_goal  # Checkmark if steps met
    filtered_df["Completed"] = filtered_df["Completed"].map({True: "✅", False: "❌"})
else:
    if "Completed" in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=["Completed"])  # Remove from Weekly/Monthly

# Sort leaderboard
filtered_df = filtered_df.sort_values(by="Steps", ascending=False).reset_index(drop=True)
filtered_df.insert(0, "Rank", range(1, len(filtered_df) + 1))

# Display leaderboard
st.table(filtered_df[["Rank", "Name", "Steps"] + (["Completed"] if show_completed else [])])

# Search for user profile
st.subheader("🔍 Search User Profile")
search_name = st.text_input("Enter name to view their progress:")

if search_name:
    search_name = search_name.strip().title()
    user_data = leaderboard_df[leaderboard_df["Name"] == search_name]
    if not user_data.empty:
        st.write(f"### Step History for {search_name}")
        user_data = user_data.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)
        user_data["Completed"] = user_data["Steps"] >= step_goal
        user_data["Completed"] = user_data["Completed"].map({True: "✔", False: "❌"})
        st.table(user_data[["Timestamp", "Steps", "Proof", "Completed"]])
    else:
        st.warning("User not found. Try a different name.")