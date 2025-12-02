import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import calendar

# Page configuration
st.set_page_config(page_title="Tuition Management System", page_icon="📚", layout="wide")

# Initialize session state for data persistence
if 'students' not in st.session_state:
    st.session_state.students = []
if 'attendance' not in st.session_state:
    st.session_state.attendance = []

# Helper functions
def save_data():
    """Save data to JSON files"""
    with open('students.json', 'w') as f:
        json.dump(st.session_state.students, f)
    with open('attendance.json', 'w') as f:
        json.dump(st.session_state.attendance, f)

def load_data():
    """Load data from JSON files"""
    try:
        with open('students.json', 'r') as f:
            st.session_state.students = json.load(f)
        with open('attendance.json', 'r') as f:
            st.session_state.attendance = json.load(f)
    except FileNotFoundError:
        pass

def get_students_for_day(day_name):
    """Get students scheduled for a specific day"""
    return [s for s in st.session_state.students if day_name in s['days']]

def check_fee_status(student, month, year):
    """Check if fee is paid for a specific month"""
    return any(
        p['month'] == month and p['year'] == year 
        for p in student.get('fees_paid', [])
    )

# Load data on startup
load_data()

# Title
st.title("📚 Tuition Management System")

# Sidebar navigation
menu = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Manage Students", "Attendance", "Fee Management", "Reports"]
)

# Dashboard
if menu == "Dashboard":
    st.header("📊 Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Students", len(st.session_state.students))
    
    with col2:
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_earnings = sum(
            float(s['monthly_fee']) 
            for s in st.session_state.students 
            if check_fee_status(s, current_month, current_year)
        )
        st.metric("Monthly Earnings", f"₹{monthly_earnings:,.2f}")
    
    with col3:
        total_expected = sum(float(s['monthly_fee']) for s in st.session_state.students)
        pending_fees = total_expected - monthly_earnings
        st.metric("Pending Fees", f"₹{pending_fees:,.2f}")
    
    st.divider()
    
    # Today's schedule
    st.subheader("Today's Schedule")
    today = datetime.now().strftime("%A")
    today_students = get_students_for_day(today)
    
    if today_students:
        for student in today_students:
            with st.container():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**{student['name']}** - {student['grade']}")
                with col2:
                    st.write(f"{student['subject']} | {student['time_slot']}")
                with col3:
                    st.write(f"₹{student['monthly_fee']}")
    else:
        st.info("No classes scheduled for today")

# Manage Students
elif menu == "Manage Students":
    st.header("👨‍🎓 Manage Students")
    
    tab1, tab2 = st.tabs(["Add/Edit Student", "View All Students"])
    
    with tab1:
        st.subheader("Add New Student")
        
        with st.form("student_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Student Name *")
                grade = st.text_input("Grade (e.g., 5th, 10th) *")
                subject = st.text_input("Subject *")
            
            with col2:
                time_slot = st.text_input("Time Slot (e.g., 4:00 PM - 5:00 PM) *")
                monthly_fee = st.number_input("Monthly Fee (₹) *", min_value=0, step=100)
                contact = st.text_input("Contact Number")
            
            st.write("**Select Days:**")
            days = []
            cols = st.columns(7)
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for i, day in enumerate(day_names):
                with cols[i]:
                    if st.checkbox(day[:3], key=f"day_{day}"):
                        days.append(day)
            
            submitted = st.form_submit_button("Add Student")
            
            if submitted:
                if name and grade and subject and time_slot and monthly_fee and days:
                    new_student = {
                        'id': len(st.session_state.students) + 1,
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
                    st.success(f"Student {name} added successfully!")
                    st.rerun()
                else:
                    st.error("Please fill all required fields and select at least one day")
    
    with tab2:
        st.subheader("All Students")
        
        if st.session_state.students:
            for idx, student in enumerate(st.session_state.students):
                with st.expander(f"{student['name']} - {student['grade']} ({student['subject']})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Days:** {', '.join(student['days'])}")
                        st.write(f"**Time Slot:** {student['time_slot']}")
                        st.write(f"**Monthly Fee:** ₹{student['monthly_fee']}")
                        if student['contact']:
                            st.write(f"**Contact:** {student['contact']}")
                    with col2:
                        if st.button("Delete", key=f"del_{student['id']}"):
                            st.session_state.students.pop(idx)
                            save_data()
                            st.success("Student deleted!")
                            st.rerun()
        else:
            st.info("No students added yet")

# Attendance
elif menu == "Attendance":
    st.header("✅ Attendance Tracking")
    
    selected_date = st.date_input("Select Date", value=date.today())
    day_name = selected_date.strftime("%A")
    
    st.subheader(f"Students Scheduled for {selected_date.strftime('%B %d, %Y')} ({day_name})")
    
    scheduled_students = get_students_for_day(day_name)
    
    if scheduled_students:
        for student in scheduled_students:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    st.write(f"**{student['name']}** - {student['grade']}")
                    st.write(f"{student['subject']} | {student['time_slot']}")
                
                # Check existing attendance
                existing_attendance = next(
                    (a for a in st.session_state.attendance 
                     if a['student_id'] == student['id'] and a['date'] == str(selected_date)),
                    None
                )
                
                current_status = existing_attendance['status'] if existing_attendance else None
                
                with col2:
                    if st.button("✅ Present", key=f"present_{student['id']}_{selected_date}", 
                                type="primary" if current_status == "present" else "secondary"):
                        # Remove existing record if any
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
                
                with col3:
                    if st.button("❌ Absent", key=f"absent_{student['id']}_{selected_date}",
                                type="primary" if current_status == "absent" else "secondary"):
                        # Remove existing record if any
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
                
                if current_status:
                    st.success(f"Status: {current_status.upper()}")
                
                st.divider()
    else:
        st.info("No classes scheduled for this date")

# Fee Management
elif menu == "Fee Management":
    st.header("💰 Fee Management")
    
    search = st.text_input("🔍 Search Student")
    
    current_month = datetime.now().month
    current_year = datetime.now().year
    month_name = calendar.month_name[current_month]
    
    st.subheader(f"Fee Status for {month_name} {current_year}")
    
    filtered_students = [
        s for s in st.session_state.students 
        if search.lower() in s['name'].lower() or not search
    ]
    
    if filtered_students:
        for student in filtered_students:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 2])
                
                with col1:
                    st.write(f"**{student['name']}** - {student['grade']}")
                    st.write(f"Monthly Fee: ₹{student['monthly_fee']}")
                
                is_paid = check_fee_status(student, current_month, current_year)
                
                with col2:
                    if is_paid:
                        st.success("✅ Paid")
                    else:
                        st.error("❌ Pending")
                
                with col3:
                    if not is_paid:
                        if st.button("Mark as Paid", key=f"pay_{student['id']}"):
                            if 'fees_paid' not in student:
                                student['fees_paid'] = []
                            student['fees_paid'].append({
                                'month': current_month,
                                'year': current_year,
                                'date': datetime.now().isoformat(),
                                'amount': student['monthly_fee']
                            })
                            save_data()
                            st.success("Fee marked as paid!")
                            st.rerun()
                
                st.divider()
    else:
        st.info("No students found")

# Reports
elif menu == "Reports":
    st.header("📈 Reports")
    
    tab1, tab2 = st.tabs(["Attendance Report", "Fee Report"])
    
    with tab1:
        st.subheader("Attendance Report")
        
        if st.session_state.attendance:
            df = pd.DataFrame(st.session_state.attendance)
            df['date'] = pd.to_datetime(df['date'])
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("From Date", value=date.today().replace(day=1))
            with col2:
                end_date = st.date_input("To Date", value=date.today())
            
            # Filter data
            mask = (df['date'] >= pd.to_datetime(start_date)) & (df['date'] <= pd.to_datetime(end_date))
            filtered_df = df[mask]
            
            if not filtered_df.empty:
                st.dataframe(
                    filtered_df[['student_name', 'date', 'status']].sort_values('date', ascending=False),
                    use_container_width=True
                )
                
                # Summary
                st.subheader("Summary")
                col1, col2 = st.columns(2)
                with col1:
                    present_count = len(filtered_df[filtered_df['status'] == 'present'])
                    st.metric("Total Present", present_count)
                with col2:
                    absent_count = len(filtered_df[filtered_df['status'] == 'absent'])
                    st.metric("Total Absent", absent_count)
            else:
                st.info("No attendance records for selected date range")
        else:
            st.info("No attendance records available")
    
    with tab2:
        st.subheader("Fee Collection Report")
        
        if st.session_state.students:
            fee_data = []
            for student in st.session_state.students:
                for payment in student.get('fees_paid', []):
                    fee_data.append({
                        'Student': student['name'],
                        'Month': calendar.month_name[payment['month']],
                        'Year': payment['year'],
                        'Amount': payment['amount'],
                        'Date': payment['date'][:10]
                    })
            
            if fee_data:
                df_fees = pd.DataFrame(fee_data)
                st.dataframe(df_fees, use_container_width=True)
                
                total_collected = df_fees['Amount'].sum()
                st.metric("Total Collected", f"₹{total_collected:,.2f}")
            else:
                st.info("No fee payments recorded yet")
        else:
            st.info("No students added yet")

# Footer
st.sidebar.divider()
st.sidebar.info("💡 Tip: All data is automatically saved!")
