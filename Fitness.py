import streamlit as st
import pandas as pd
import os
from datetime import datetime
import random

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

# Admin authentication setup
ADMIN_CREDENTIALS = {"admin": "securepassword123"}  # Change password for security
admin_username = st.sidebar.text_input("Username", value="", type="password")
admin_password = st.sidebar.text_input("Password", value="", type="password")
is_admin = admin_username in ADMIN_CREDENTIALS and admin_password == ADMIN_CREDENTIALS.get(admin_username)

# Admin logout button
if is_admin:
    if st.sidebar.button("Log Out"):
        st.session_state.pop("admin_username", None)
        st.session_state.pop("admin_password", None)
        st.session_state.pop("is_admin", None)
        st.rerun()

# Streamlit UI
st.image("morphworkslogo4.png", width=650)
st.title("Marchin' Into Spring 2025 Challenge")
st.write("Upload a screenshot of your step count and enter the total steps below.")

# Generate a new step goal every day
today_date = datetime.now().date()
step_goal_file = "daily_goal.txt"

if os.path.exists(step_goal_file):
    with open(step_goal_file, "r") as f:
        content = f.read().strip()

    if "," in content:  # Ensure the file has both date and step goal
        saved_date, saved_goal = content.split(",")

        if saved_date == str(today_date):
            step_goal = int(saved_goal)
        else:
            step_goal = random.randint(5000, 15000)
            with open(step_goal_file, "w") as f:
                f.write(f"{today_date},{step_goal}")
    else:
        step_goal = random.randint(5000, 15000)
        with open(step_goal_file, "w") as f:
            f.write(f"{today_date},{step_goal}")
else:
    step_goal = random.randint(5000, 15000)
    with open(step_goal_file, "w") as f:
        f.write(f"{today_date},{step_goal}")

# Display step goal
st.markdown(f"### 🏆 Today's Step Goal: {step_goal} steps")

# User input fields
name = st.selectbox("Select Your Name or Enter a New One:", 
                    options=["Enter New Name"] + sorted(leaderboard_df["Name"].unique().tolist()))

if name == "Enter New Name":
    name = st.text_input("Enter your name:")

steps = st.number_input("Enter your steps for today", min_value=1, step=1)
uploaded_file = st.file_uploader("Upload step count screenshot (optional)", type=["jpg", "png", "jpeg"])

# Submit button
if st.button("Submit Steps"):
    if name:
        # Standardize the name before saving (title-case)
        name = name.strip().lower().title()

        # Save proof image
        proof_filename = None
        if uploaded_file:
            proof_filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            with open(os.path.join(UPLOAD_DIR, proof_filename), "wb") as f:
                f.write(uploaded_file.getbuffer())

        # Check if step goal was met
        completed = steps >= step_goal

        # Ensure Timestamp column is in datetime format
        leaderboard_df["Timestamp"] = pd.to_datetime(leaderboard_df["Timestamp"], errors="coerce")

        # Exclude relevant entries before the concat operation
        today_date = datetime.now().date()
        leaderboard_df = leaderboard_df[~((leaderboard_df["Name"] == name) & (leaderboard_df["Timestamp"].dt.date == today_date))]

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
        start_of_week = now - pd.Timedelta(days=now.weekday())  # Get the start of the current week (Monday)
        filtered_df = leaderboard_df[leaderboard_df["Timestamp"] >= start_of_week]
    elif leaderboard_view == "Monthly":
        filtered_df = leaderboard_df[leaderboard_df["Timestamp"] >= now - pd.Timedelta(days=30)]
    else:
        filtered_df = leaderboard_df
    show_completed = False  # Hide checkmarks and Xs

# Only show "Completed" column for Daily view
if show_completed:
    filtered_df["Completed"] = filtered_df["Steps"] >= step_goal  # Checkmark if steps met
    filtered_df["Completed"] = filtered_df["Completed"].map({True: "✅", False: "❌"})
else:
    if "Completed" in filtered_df.columns:
        filtered_df = filtered_df.drop(columns=["Completed"])  # Remove from Weekly/Monthly

# Sort leaderboard
filtered_df = filtered_df.sort_values(by="Timestamp", ascending=True).reset_index(drop=True)
filtered_df.insert(0, "Rank", range(1, len(filtered_df) + 1))

# Display leaderboard
st.table(filtered_df[["Rank", "Name", "Steps", "Timestamp"] + (["Completed"] if show_completed else [])])

# Search for user profile
st.subheader("🔍 Search User Profile")
search_name = st.text_input("Enter name to view their progress:")

if search_name:
    # Standardize the name before searching (title-case)
    search_name = search_name.strip().title()

    # Filter the DataFrame based on the formatted name
    user_data = leaderboard_df[leaderboard_df["Name"] == search_name]

    if not user_data.empty:
        st.write(f"### Step History for {search_name}")
        
        # Sort the user data by Timestamp in ascending order (oldest first)
        user_data = user_data.sort_values(by="Timestamp", ascending=True).reset_index(drop=True)
        
        # Add the "Completed" column
        user_data["Completed"] = user_data["Steps"] >= step_goal
        user_data["Completed"] = user_data["Completed"].map({True: "✔", False: "❌"})
        
        # For each step entry, show the timestamp, steps, completion status, and clickable link to proof
        for index, row in user_data.iterrows():
            timestamp = row['Timestamp']
            steps = row['Steps']
            completed = row['Completed']
            proof_filename = row['Proof']
            
            # Display details for the entry (timestamp, steps, completion status)
            st.write(f"**{timestamp}** | **{steps} steps** | {completed}")
            
            # If proof exists, display the clickable proof link
            if proof_filename != "No Proof":
                proof_link = f'<a href="/uploads/{proof_filename}" target="_blank">View proof</a>'
                st.markdown(proof_link, unsafe_allow_html=True)
                
                # Optionally, display the image inline as well
                st.image(f"uploads/{proof_filename}", caption=f"Proof for {row['Name']} at {timestamp}", use_column_width=True)
    else:
        st.warning("No records found for this user. Please try again with a different name.")
           
