import streamlit as st
from streamlit_calendar import calendar
import json
import os
from datetime import datetime

# Set page layout to wide for an expansive, Apple Calendar-like view
st.set_page_config(layout="wide")

DB_FILE = "calendar_data.json"
USER_DB = "users.json"

# --- DATABASE FUNCTIONS ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {} # Stores {username: [events]}

def save_data(all_data):
    with open(DB_FILE, "w") as f:
        json.dump(all_data, f, indent=4)

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {} # Stores {username: password}

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=4)

# Initialize master data in session state
if "all_calendar_data" not in st.session_state:
    st.session_state.all_calendar_data = load_data()

if "users" not in st.session_state:
    st.session_state.users = load_users()

# Initialize authentication state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None


# --- LOGIN / REGISTRATION UI ---
if not st.session_state.authenticated:
    st.title("🔐 FocusFlow Portal")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to your account")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Login", type="primary"):
            users = st.session_state.users
            if login_user in users and users[login_user] == login_pass:
                st.session_state.authenticated = True
                st.session_state.username = login_user
                st.success(f"Welcome back, {login_user}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
                
    with tab2:
        st.subheader("Create a new account")
        reg_user = st.text_input("Choose a Username", key="reg_user").strip()
        reg_pass = st.text_input("Choose a Password", type="password", key="reg_pass")
        
        if st.button("Register"):
            if not reg_user or not reg_pass:
                st.error("Please fill in all fields.")
            elif reg_user in st.session_state.users:
                st.error("Username already exists. Try another one.")
            else:
                st.session_state.users[reg_user] = reg_pass
                save_users(st.session_state.users)
                st.success("Account created successfully! You can now log in.")

# --- MAIN APP UI (Only visible if logged in) ---
else:
    current_user = st.session_state.username
    if current_user not in st.session_state.all_calendar_data:
        st.session_state.all_calendar_data[current_user] = []
        
    user_events = st.session_state.all_calendar_data[current_user]

    # --- SIDEBAR (SETTINGS & DELETION) ---
    with st.sidebar:
        st.header("⚙️ Account Settings")
        st.write(f"Logged in as: **{current_user}**")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()
            
        st.write("---")
        st.subheader("🚨 Danger Zone")
        
        # Checkbox acting as a safety confirmation hurdle
        confirm_delete = st.checkbox("I want to permanently delete my account and calendar data.")
        
        if st.button("Delete My Account", type="primary", disabled=not confirm_delete, use_container_width=True):
            # 1. Remove calendar data entries
            if current_user in st.session_state.all_calendar_data:
                del st.session_state.all_calendar_data[current_user]
                save_data(st.session_state.all_calendar_data)
            
            # 2. Remove user profile credentials
            if current_user in st.session_state.users:
                del st.session_state.users[current_user]
                save_users(st.session_state.users)
                
            # 3. Clean up the application state session tracking variables
            st.session_state.authenticated = False
            st.session_state.username = None
            
            st.toast("Your account has been deleted permanently.")
            st.rerun()

    # --- TOP NAV BAR ---
    st.title("📅 FocusFlow")
    st.subheader(f"Welcome back, {current_user}! Your centralized timetable and tracker.")
    st.write("---")

    # Create two columns: Left for input data/deletions, Right for the Calendar display
    col1, col2 = st.columns([1, 3])

    with col1:
        st.header("📝 Add New Event")
        
        event_type = st.radio("Event Type", ["Class/Timetable", "Assignment Due"])
        title = st.text_input("Title / Course Code", placeholder="e.g., CS101 Lecture")
        
        start_date = st.date_input("Date")
        color = "#FF3B30" if event_type == "Assignment Due" else "#34C759"
        
        if event_type == "Class/Timetable":
            start_time = st.time_input("Start Time")
            end_time = st.time_input("End Time")
            
            start_iso = f"{start_date}T{start_time}"
            end_iso = f"{start_date}T{end_time}"
            is_all_day = False
        else:
            start_iso = f"{start_date}"
            end_iso = f"{start_date}"
            is_all_day = True
        
        if st.button("Add to Calendar", use_container_width=True):
            if title:
                new_event = {
                    "title": f"[{event_type.split('/')[0]}] {title}",
                    "start": start_iso,
                    "end": end_iso,
                    "backgroundColor": color,
                    "borderColor": color,
                    "allDay": is_all_day
                }
                st.session_state.all_calendar_data[current_user].append(new_event)
                save_data(st.session_state.all_calendar_data)
                st.success("Event added successfully!")
                st.rerun()
            else:
                st.error("Please enter a title.")

    with col2:
        # --- CALENDAR CONFIGURATION ---
        calendar_options = {
            "editable": True,
            "selectable": True,
            "timeZone": "UTC",
            "showNonCurrentDates": False,
            "initialView": "dayGridMonth",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth",
            },
        }
        
        calendar_state = calendar(
            events=user_events,
            options=calendar_options,
            key="student_calendar"
        )
        
        # --- INDIVIDUAL DELETE LOGIC ---
        if calendar_state.get("eventClick"):
            clicked_info = calendar_state["eventClick"]["event"]
            clicked_title = clicked_info.get("title")
            clicked_start = clicked_info.get("start")
            
            st.write("---")
            st.warning(f"🗑️ **Selected Event:** {clicked_title}")
            
            if st.button("Delete Selected Event", type="primary"):
                updated_events = [
                    e for e in user_events 
                    if not (e["title"] == clicked_title and e["start"].startswith(clicked_start[:10]))
                ]
                st.session_state.all_calendar_data[current_user] = updated_events
                save_data(st.session_state.all_calendar_data)
                st.success("Event removed!")
                st.rerun()
                
        st.write("---")
        if st.button("Clear My Events"):
            st.session_state.all_calendar_data[current_user] = []
            save_data(st.session_state.all_calendar_data)
            st.rerun()