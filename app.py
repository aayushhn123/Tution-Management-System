import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, timedelta
import calendar

# Page configuration - Mobile optimized
st.set_page_config(
    page_title="Tuition Tracker",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly UI
st.markdown("""
<style>
    .stMarkdown, .stText {
        font-size: 18px !important;
    }
    
    .stButton > button {
        height: 60px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        width: 100% !important;
        border-radius: 12px !important;
        margin: 5px 0 !important;
    }
    
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select,
    .stTextArea > div > div > textarea {
        font-size: 18px !important;
        height: 55px !important;
        padding: 12px !important;
    }
    
    .stTextArea > div > div > textarea {
        height: 100px !important;
    }
    
    .stCheckbox {
        font-size: 18px !important;
    }
    
    .stCheckbox > label > div {
        font-size: 18px !important;
    }
    
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 18px !important;
    }
    
    .stDateInput > div > div > input {
        font-size: 18px !important;
        height: 55px !important;
    }
    
    .stRadio > label {
        font-size: 18px !important;
    }
    
    .streamlit-expanderHeader {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    
    .stSuccess, .stError, .stWarning, .stInfo {
        font-size: 18px !important;
        padding: 15px !important;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px !important;
        padding: 15px 20px !important;
    }
    
    hr {
        margin: 20px 0 !important;
    }
    
    /* Day selection boxes */
    .day-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border: 3px solid #e0e0e0;
    }
    
    .day-box-selected {
        background-color: #d4edda;
        border: 3px solid #28a745;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'students' not in st.session_state:
    st.session_state.students = []
if 'attendance' not in st.session_state:
    st.session_state.attendance = []
if 'reschedules' not in st.session_state:
    st.session_state.reschedules = []
if 'selected_days' not in st.session_state:
    st.session_state.selected_days = {}

# Helper functions
def save_data():
    """Save data to JSON files"""
    try:
        with open('students.json', 'w') as f:
            json.dump(st.session_state.students, f)
        with open('attendance.json', 'w') as f:
            json.dump(st.session_state.attendance, f)
        with open('reschedules.json', 'w') as f:
            json.dump(st.session_state.reschedules, f)
    except Exception as e:
        st.error(f"Error saving data: {e}")

def load_data():
    """Load data from JSON files"""
    try:
        with open('students.json', 'r') as f:
            st.session_state.students = json.load(f)
        with open('attendance.json', 'r') as f:
            st.session_state.attendance = json.load(f)
        with open('reschedules.json', 'r') as f:
            st.session_state.reschedules = json.load(f)
    except FileNotFoundError:
        pass

def get_time_for_day(student, day_name):
    """Get the time slot for a specific day"""
    if isinstance(student.get('time_slot'), dict):
        return student['time_slot'].get(day_name, "Not scheduled")
    else:
        return student.get('time_slot', "Not scheduled")

def get_students_for_day(day_name, check_date=None):
    """Get students scheduled for a specific day"""
    base_students = []
    for s in st.session_state.students:
        if isinstance(s.get('time_slot'), dict):
            if day_name in s['time_slot']:
                base_students.append(s)
        else:
            if day_name in s.get('days', []):
                base_students.append(s)
    
    if check_date:
        date_str = str(check_date)
        
        rescheduled_to = [
            next(st for st in st.session_state.students if st['id'] == r['student_id'])
            for r in st.session_state.reschedules
            if r['new_date'] == date_str and r['status'] == 'active'
        ]
        
        rescheduled_from_ids = [
            r['student_id'] for r in st.session_state.reschedules
            if r['original_date'] == date_str and r['status'] == 'active'
        ]
        
        base_students = [s for s in base_students if s['id'] not in rescheduled_from_ids]
        base_students.extend(rescheduled_to)
    
    return base_students

def check_fee_status(student, month, year):
    """Check if fee is paid"""
    return any(
        p['month'] == month and p['year'] == year 
        for p in student.get('fees_paid', [])
    )

# Load data on startup
load_data()

# Simple mobile-friendly navigation with emoji buttons
st.title("📚 My Tuition Classes")

# Big, clear navigation buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🏠 Today's Classes", use_container_width=True):
        st.session_state.page = "home"
    if st.button("➕ Add Student", use_container_width=True):
        st.session_state.page = "add_student"
        st.session_state.selected_days = {}
    if st.button("✅ Attendance", use_container_width=True):
        st.session_state.page = "attendance"

with col2:
    if st.button("💰 Fees", use_container_width=True):
        st.session_state.page = "fees"
    if st.button("🔄 Reschedule", use_container_width=True):
        st.session_state.page = "reschedule"
    if st.button("📋 All Students", use_container_width=True):
        st.session_state.page = "students"

# Initialize page
if 'page' not in st.session_state:
    st.session_state.page = "home"

st.markdown("---")

# HOME / TODAY'S CLASSES
if st.session_state.page == "home":
    st.header("📅 Today's Schedule")
    
    today = datetime.now().strftime("%A")
    today_date = date.today()
    
    st.info(f"📆 {today_date.strftime('%d %B %Y')} ({today})")
    
    today_students = get_students_for_day(today, today_date)
    
    if today_students:
        st.subheader(f"Total {len(today_students)} Classes Today")
        
        for student in today_students:
            with st.container():
                st.markdown(f"### 👨‍🎓 {student['name']}")
                st.markdown(f"**Grade:** {student['grade']}")
                st.markdown(f"**Subject:** {student['subject']}")
                
                reschedule = next(
                    (r for r in st.session_state.reschedules 
                     if r['student_id'] == student['id'] and r['new_date'] == str(today_date) and r['status'] == 'active'),
                    None
                )
                
                if reschedule:
                    st.markdown(f"**Time:** {reschedule['new_time']} 🔄")
                    st.warning(f"Rescheduled from {reschedule['original_date']}")
                else:
                    time_slot = get_time_for_day(student, today)
                    st.markdown(f"**Time:** {time_slot}")
                
                st.markdown(f"**Fee:** ₹{student['monthly_fee']}")
                
                st.markdown("---")
    else:
        st.success("🎉 No classes today!")
    
    st.markdown("---")
    st.subheader("📊 This Month")
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    col1, col2 = st.columns(2)
    with col1:
        total_students = len(st.session_state.students)
        st.metric("Total Students", total_students)
    
    with col2:
        monthly_earnings = sum(
            float(s['monthly_fee']) 
            for s in st.session_state.students 
            if check_fee_status(s, current_month, current_year)
        )
        st.metric("Fees Received", f"₹{monthly_earnings:,.0f}")

# ADD STUDENT
elif st.session_state.page == "add_student":
    st.header("➕ Add New Student")
    
    st.subheader("📝 Basic Details")
    
    name = st.text_input("Name *", placeholder="Example: Rahul Sharma")
    
    grade = st.text_input("Grade *", placeholder="Example: 8th, 10th")
    
    subject = st.text_input("Subject *", placeholder="Example: Math, Science")
    
    monthly_fee = st.number_input("Monthly Fee (₹) *", min_value=0, step=100, value=0)
    
    contact = st.text_input("Phone Number (Optional)", placeholder="Example: 9876543210")
    
    st.markdown("---")
    st.subheader("📅 Select Class Days & Times")
    st.caption("Tap on days when class is scheduled")
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    # Display days as big buttons
    for day in day_names:
        is_selected = day in st.session_state.selected_days
        
        col1, col2 = st.columns([2, 3])
        
        with col1:
            button_label = f"{'✅' if is_selected else '⬜'} {day}"
            if st.button(button_label, key=f"btn_{day}", use_container_width=True):
                if day in st.session_state.selected_days:
                    del st.session_state.selected_days[day]
                else:
                    st.session_state.selected_days[day] = ""
                st.rerun()
        
        with col2:
            if is_selected:
                time_input = st.text_input(
                    "Time",
                    value=st.session_state.selected_days[day],
                    placeholder="e.g., 4:00 PM - 5:00 PM",
                    key=f"time_{day}",
                    label_visibility="collapsed"
                )
                st.session_state.selected_days[day] = time_input
    
    st.markdown("---")
    
    # Show selected schedule
    if st.session_state.selected_days:
        st.info(f"✅ Selected {len(st.session_state.selected_days)} days")
        for day, time in st.session_state.selected_days.items():
            if time:
                st.caption(f"• {day}: {time}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Add Student", type="primary", use_container_width=True):
            # Validate inputs
            schedule = {day: time for day, time in st.session_state.selected_days.items() if time.strip()}
            
            if name and grade and subject and monthly_fee > 0 and schedule:
                new_student = {
                    'id': len(st.session_state.students) + 1 if st.session_state.students else 1,
                    'name': name,
                    'grade': grade,
                    'subject': subject,
                    'time_slot': schedule,
                    'monthly_fee': monthly_fee,
                    'contact': contact,
                    'fees_paid': []
                }
                st.session_state.students.append(new_student)
                save_data()
                st.session_state.selected_days = {}
                st.success(f"✅ {name} added successfully!")
                st.balloons()
                if st.button("🏠 Go to Home", use_container_width=True):
                    st.session_state.page = "home"
                    st.rerun()
            else:
                st.error("⚠️ Please fill all fields and add time for selected days!")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.selected_days = {}
            st.session_state.page = "home"
            st.rerun()

# ATTENDANCE
elif st.session_state.page == "attendance":
    st.header("✅ Attendance")
    
    selected_date = st.date_input("Select Date", value=date.today())
    day_name = selected_date.strftime("%A")
    
    st.info(f"📆 {selected_date.strftime('%d %B %Y')} ({day_name})")
    
    scheduled_students = get_students_for_day(day_name, selected_date)
    
    if scheduled_students:
        st.subheader(f"Total {len(scheduled_students)} Students")
        
        for student in scheduled_students:
            with st.container():
                st.markdown(f"### 👨‍🎓 {student['name']}")
                st.markdown(f"**Grade:** {student['grade']}")
                st.markdown(f"**Subject:** {student['subject']}")
                
                reschedule = next(
                    (r for r in st.session_state.reschedules 
                     if r['student_id'] == student['id'] and r['new_date'] == str(selected_date) and r['status'] == 'active'),
                    None
                )
                
                if reschedule:
                    st.markdown(f"**Time:** {reschedule['new_time']} 🔄")
                else:
                    time_slot = get_time_for_day(student, day_name)
                    st.markdown(f"**Time:** {time_slot}")
                
                existing_attendance = next(
                    (a for a in st.session_state.attendance 
                     if a['student_id'] == student['id'] and a['date'] == str(selected_date)),
                    None
                )
                
                current_status = existing_attendance['status'] if existing_attendance else None
                
                col1, col2 = st.columns(2)
                
                with col1:
                    present_type = "primary" if current_status == "present" else "secondary"
                    if st.button(f"✅ Present", 
                                key=f"present_{student['id']}_{selected_date}",
                                type=present_type,
                                use_container_width=True):
                        st.session_state.attendance = [
                            a for a in st.session_state.attendance 
                            if not (a['student_id'] == student['id'] and a['date'] == str(selected_date))
                        ]
                        st.session_state.attendance.append({
                            'student_id': student['id'],
                            'student_name': student['name'],
                            'date': str(selected_date),
                            'status': 'present',
                            'timestamp': datetime.now().isoformat()
                        })
                        save_data()
                        st.rerun()
                
                with col2:
                    absent_type = "primary" if current_status == "absent" else "secondary"
                    if st.button(f"❌ Absent",
                                key=f"absent_{student['id']}_{selected_date}",
                                type=absent_type,
                                use_container_width=True):
                        st.session_state.attendance = [
                            a for a in st.session_state.attendance 
                            if not (a['student_id'] == student['id'] and a['date'] == str(selected_date))
                        ]
                        st.session_state.attendance.append({
                            'student_id': student['id'],
                            'student_name': student['name'],
                            'date': str(selected_date),
                            'status': 'absent',
                            'timestamp': datetime.now().isoformat()
                        })
                        save_data()
                        st.rerun()
                
                if current_status == "present":
                    st.success("✅ Present")
                elif current_status == "absent":
                    st.error("❌ Absent")
                
                st.markdown("---")
    else:
        st.info("No classes on this day")

# FEES
elif st.session_state.page == "fees":
    st.header("💰 Fees")
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    month_name = calendar.month_name[current_month]
    
    st.subheader(f"📅 {month_name} {current_year}")
    
    if st.session_state.students:
        total_expected = sum(float(s['monthly_fee']) for s in st.session_state.students)
        total_received = sum(
            float(s['monthly_fee']) 
            for s in st.session_state.students 
            if check_fee_status(s, current_month, current_year)
        )
        total_pending = total_expected - total_received
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", f"₹{total_expected:,.0f}")
        with col2:
            st.metric("Received", f"₹{total_received:,.0f}")
        with col3:
            st.metric("Pending", f"₹{total_pending:,.0f}")
        
        st.markdown("---")
        
        for student in st.session_state.students:
            with st.container():
                st.markdown(f"### 👨‍🎓 {student['name']}")
                st.markdown(f"**Grade:** {student['grade']}")
                st.markdown(f"**Monthly Fee:** ₹{student['monthly_fee']}")
                
                is_paid = check_fee_status(student, current_month, current_year)
                
                if is_paid:
                    st.success("✅ Fee Received")
                else:
                    st.error("❌ Fee Pending")
                    
                    if st.button(f"💰 Mark Paid", 
                                key=f"pay_{student['id']}",
                                use_container_width=True):
                        if 'fees_paid' not in student:
                            student['fees_paid'] = []
                        student['fees_paid'].append({
                            'month': current_month,
                            'year': current_year,
                            'date': datetime.now().isoformat(),
                            'amount': student['monthly_fee']
                        })
                        save_data()
                        st.success("✅ Fee marked as paid!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No students added yet")

# RESCHEDULE
elif st.session_state.page == "reschedule":
    st.header("🔄 Reschedule Class")
    
    if st.session_state.students:
        st.subheader("1️⃣ Select Student")
        
        student_names = [f"{s['name']} - {s['grade']}" for s in st.session_state.students]
        selected_index = st.selectbox(
            "Choose student",
            range(len(student_names)),
            format_func=lambda x: student_names[x],
            label_visibility="collapsed"
        )
        
        student = st.session_state.students[selected_index]
        
        # Show schedule
        st.info("📅 Regular Schedule:")
        if isinstance(student['time_slot'], dict):
            for day, time in student['time_slot'].items():
                st.caption(f"• {day}: {time}")
        else:
            st.caption(f"Days: {', '.join(student.get('days', []))}, Time: {student['time_slot']}")
        
        st.markdown("---")
        st.subheader("2️⃣ Select Dates")
        
        original_date = st.date_input(
            "From Date (Original) *",
            min_value=date.today(),
            help="Which class to reschedule"
        )
        
        new_date = st.date_input(
            "To Date (New) *",
            min_value=date.today(),
            help="New date for the class"
        )
        
        st.markdown("---")
        st.subheader("3️⃣ New Time (Optional)")
        
        new_time = st.text_input(
            "Enter new time or leave empty",
            placeholder="e.g., 5:00 PM - 6:00 PM"
        )
        
        reason = st.text_area(
            "Reason (Optional)",
            placeholder="Holiday, Sick, etc."
        )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Reschedule", type="primary", use_container_width=True):
                original_day = original_date.strftime("%A")
                default_time = get_time_for_day(student, original_day)
                
                new_reschedule = {
                    'id': len(st.session_state.reschedules) + 1,
                    'student_id': student['id'],
                    'student_name': student['name'],
                    'original_date': str(original_date),
                    'new_date': str(new_date),
                    'new_time': new_time if new_time else default_time,
                    'reason': reason,
                    'status': 'active',
                    'created_at': datetime.now().isoformat()
                }
                st.session_state.reschedules.append(new_reschedule)
                save_data()
                st.success(f"✅ Class rescheduled!")
                st.balloons()
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()
    else:
        st.info("Add students first")
        if st.button("➕ Add Student", use_container_width=True):
            st.session_state.page = "add_student"
            st.rerun()

# ALL STUDENTS
elif st.session_state.page == "students":
    st.header("📋 All Students")
    
    if st.session_state.students:
        st.subheader(f"Total {len(st.session_state.students)} Students")
        
        for idx, student in enumerate(st.session_state.students):
            with st.container():
                st.markdown(f"### 👨‍🎓 {student['name']}")
                st.markdown(f"**Grade:** {student['grade']}")
                st.markdown(f"**Subject:** {student['subject']}")
                
                # Display schedule
                st.markdown("**Schedule:**")
                if isinstance(student['time_slot'], dict):
                    for day, time in student['time_slot'].items():
                        st.caption(f"• {day}: {time}")
                else:
                    st.caption(f"Days: {', '.join(student.get('days', []))}")
                    st.caption(f"Time: {student['time_slot']}")
                
                st.markdown(f"**Monthly Fee:** ₹{student['monthly_fee']}")
                if student['contact']:
                    st.markdown(f"**Phone:** {student['contact']}")
                
                if st.button(f"🗑️ Delete {student['name']}", 
                           key=f"del_{student['id']}",
                           use_container_width=True):
                    if st.button(f"⚠️ Confirm Delete?", 
                               key=f"confirm_del_{student['id']}",
                               type="primary",
                               use_container_width=True):
                        st.session_state.students.pop(idx)
                        save_data()
                        st.success("✅ Student deleted!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("No students added yet")
        if st.button("➕ Add Student", use_container_width=True):
            st.session_state.page = "add_student"
            st.rerun()

# Footer
st.markdown("---")
st.caption("💾 All data is automatically saved")
st.caption("Made with ❤️ for Mom")
