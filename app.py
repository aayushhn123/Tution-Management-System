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
    initial_sidebar_state="collapsed"  # Better for mobile
)

# Custom CSS for mobile-friendly UI
st.markdown("""
<style>
    /* Larger text for readability */
    .stMarkdown, .stText {
        font-size: 18px !important;
    }
    
    /* Bigger buttons */
    .stButton > button {
        height: 60px !important;
        font-size: 20px !important;
        font-weight: bold !important;
        width: 100% !important;
        border-radius: 12px !important;
        margin: 5px 0 !important;
    }
    
    /* Larger input fields */
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
    
    /* Larger checkboxes */
    .stCheckbox {
        font-size: 18px !important;
    }
    
    .stCheckbox > label > div {
        font-size: 18px !important;
    }
    
    /* Better spacing for mobile */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Larger metrics */
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 18px !important;
    }
    
    /* Date picker styling */
    .stDateInput > div > div > input {
        font-size: 18px !important;
        height: 55px !important;
    }
    
    /* Radio buttons */
    .stRadio > label {
        font-size: 18px !important;
    }
    
    /* Expander text */
    .streamlit-expanderHeader {
        font-size: 18px !important;
        font-weight: bold !important;
    }
    
    /* Success/Error messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        font-size: 18px !important;
        padding: 15px !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px !important;
        padding: 15px 20px !important;
    }
    
    /* Divider spacing */
    hr {
        margin: 20px 0 !important;
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

def get_students_for_day(day_name, check_date=None):
    """Get students scheduled for a specific day"""
    base_students = [s for s in st.session_state.students if day_name in s['days']]
    
    if check_date:
        date_str = str(check_date)
        
        # Add rescheduled TO this date
        rescheduled_to = [
            next(s for s in st.session_state.students if s['id'] == r['student_id'])
            for r in st.session_state.reschedules
            if r['new_date'] == date_str and r['status'] == 'active'
        ]
        
        # Remove rescheduled FROM this date
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
    
    # Show today's date prominently
    st.info(f"📆 {today_date.strftime('%d %B %Y')} ({today})")
    
    today_students = get_students_for_day(today, today_date)
    
    if today_students:
        st.subheader(f"Total {len(today_students)} Classes Today")
        
        for student in today_students:
            # Card-like container for each student
            with st.container():
                st.markdown(f"### 👨‍🎓 {student['name']}")
                st.markdown(f"**Grade:** {student['grade']}")
                st.markdown(f"**Subject:** {student['subject']}")
                
                # Check if rescheduled
                reschedule = next(
                    (r for r in st.session_state.reschedules 
                     if r['student_id'] == student['id'] and r['new_date'] == str(today_date) and r['status'] == 'active'),
                    None
                )
                
                if reschedule:
                    st.markdown(f"**Time:** {reschedule['new_time']} 🔄")
                    st.warning(f"Rescheduled from {reschedule['original_date']}")
                else:
                    st.markdown(f"**Time:** {student['time_slot']}")
                
                st.markdown(f"**Fee:** ₹{student['monthly_fee']}")
                
                st.markdown("---")
    else:
        st.success("🎉 No classes today!")
    
    # Quick stats
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
    
    with st.form("student_form", clear_on_submit=True):
        st.subheader("Student Details")
        
        name = st.text_input("Name *", placeholder="Example: Rahul Sharma")
        
        grade = st.text_input("Grade *", placeholder="Example: 8th, 10th")
        
        subject = st.text_input("Subject *", placeholder="Example: Math, Science")
        
        time_slot = st.text_input("Time *", placeholder="Example: 4:00 PM - 5:00 PM")
        
        monthly_fee = st.number_input("Monthly Fee (₹) *", min_value=0, step=100, value=0)
        
        contact = st.text_input("Phone Number (Optional)", placeholder="Example: 9876543210")
        
        st.markdown("---")
        st.subheader("Which Days? *")
        st.caption("Select the days when class is scheduled")
        
        days = []
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day in day_names:
            if st.checkbox(f"{day}", key=f"day_{day}"):
                days.append(day)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Add Student", use_container_width=True)
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if cancelled:
            st.session_state.page = "home"
            st.rerun()
        
        if submitted:
            if name and grade and subject and time_slot and monthly_fee > 0 and days:
                new_student = {
                    'id': len(st.session_state.students) + 1 if st.session_state.students else 1,
                    'name': name,
                    'grade': grade,
                    'subject': subject,
                    'days': days,
                    'time_slot': time_slot,
                    'monthly_fee': monthly_fee,
                    'contact': contact,
                    'fees_paid': []
                }
                st.session_state.students.append(new_student)
                save_data()
                st.success(f"✅ {name} added successfully!")
                st.balloons()
                if st.button("🏠 Go to Home"):
                    st.session_state.page = "home"
                    st.rerun()
            else:
                st.error("⚠️ Please fill all required fields!")

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
                
                # Check if rescheduled
                reschedule = next(
                    (r for r in st.session_state.reschedules 
                     if r['student_id'] == student['id'] and r['new_date'] == str(selected_date) and r['status'] == 'active'),
                    None
                )
                
                if reschedule:
                    st.markdown(f"**Time:** {reschedule['new_time']} 🔄")
                else:
                    st.markdown(f"**Time:** {student['time_slot']}")
                
                # Check existing attendance
                existing_attendance = next(
                    (a for a in st.session_state.attendance 
                     if a['student_id'] == student['id'] and a['date'] == str(selected_date)),
                    None
                )
                
                current_status = existing_attendance['status'] if existing_attendance else None
                
                # Big attendance buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    present_type = "primary" if current_status == "present" else "secondary"
                    if st.button(f"✅ Present", 
                                key=f"present_{student['id']}_{selected_date}",
                                type=present_type,
                                use_container_width=True):
                        # Remove existing record
                        st.session_state.attendance = [
                            a for a in st.session_state.attendance 
                            if not (a['student_id'] == student['id'] and a['date'] == str(selected_date))
                        ]
                        # Add new record
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
                        # Remove existing record
                        st.session_state.attendance = [
                            a for a in st.session_state.attendance 
                            if not (a['student_id'] == student['id'] and a['date'] == str(selected_date))
                        ]
                        # Add new record
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
        # Calculate totals
        total_expected = sum(float(s['monthly_fee']) for s in st.session_state.students)
        total_received = sum(
            float(s['monthly_fee']) 
            for s in st.session_state.students 
            if check_fee_status(s, current_month, current_year)
        )
        total_pending = total_expected - total_received
        
        # Show summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total", f"₹{total_expected:,.0f}")
        with col2:
            st.metric("Received", f"₹{total_received:,.0f}")
        with col3:
            st.metric("Pending", f"₹{total_pending:,.0f}")
        
        st.markdown("---")
        
        # Show each student
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
        with st.form("reschedule_form", clear_on_submit=True):
            st.subheader("Select Student")
            
            # Create simple dropdown with student names
            student_names = [f"{s['name']} - {s['grade']}" for s in st.session_state.students]
            selected_index = st.selectbox(
                "Student *",
                range(len(student_names)),
                format_func=lambda x: student_names[x]
            )
            
            student = st.session_state.students[selected_index]
            
            # Show regular schedule
            st.info(f"Regular Days: {', '.join(student['days'])}\n\nTime: {student['time_slot']}")
            
            st.markdown("---")
            st.subheader("Select Dates")
            
            original_date = st.date_input(
                "Original Date *",
                min_value=date.today(),
                help="The date to reschedule from"
            )
            
            new_date = st.date_input(
                "New Date *",
                min_value=date.today(),
                help="The new date for the class"
            )
            
            new_time = st.text_input(
                "New Time (Optional)",
                placeholder="Leave empty or enter new time"
            )
            
            reason = st.text_area(
                "Reason (Optional)",
                placeholder="Example: Holiday, Student sick, etc."
            )
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button("✅ Reschedule", use_container_width=True)
            with col2:
                cancelled = st.form_submit_button("❌ Cancel", use_container_width=True)
            
            if cancelled:
                st.session_state.page = "home"
                st.rerun()
            
            if submitted:
                if original_date and new_date:
                    new_reschedule = {
                        'id': len(st.session_state.reschedules) + 1,
                        'student_id': student['id'],
                        'student_name': student['name'],
                        'original_date': str(original_date),
                        'new_date': str(new_date),
                        'new_time': new_time if new_time else student['time_slot'],
                        'reason': reason,
                        'status': 'active',
                        'created_at': datetime.now().isoformat()
                    }
                    st.session_state.reschedules.append(new_reschedule)
                    save_data()
                    st.success(f"✅ Class rescheduled!")
                    st.balloons()
                    if st.button("🏠 Go to Home"):
                        st.session_state.page = "home"
                        st.rerun()
    else:
        st.info("Add students first")
        if st.button("➕ Add Student"):
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
                st.markdown(f"**Days:** {', '.join(student['days'])}")
                st.markdown(f"**Time:** {student['time_slot']}")
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
        if st.button("➕ Add Student"):
            st.session_state.page = "add_student"
            st.rerun()

# Footer
st.markdown("---")
st.caption("💾 All data is automatically saved")
st.caption("Made with ❤️ for Mom")
