import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime, date, timedelta
import calendar

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="📚 Tuition Tracker",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# MOBILE-FRIENDLY CSS  (Streamlit elements only)
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── global typography ── */
html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }

/* ── bigger tap targets for every button ── */
.stButton > button {
    height: 52px !important;
    font-size: 17px !important;
    font-weight: 600 !important;
    border-radius: 10px !important;
    width: 100% !important;
}

/* ── primary buttons: warm orange ── */
.stButton > button[kind="primary"] {
    background: #FF6B35 !important;
    border: none !important;
    color: white !important;
}
.stButton > button[kind="primary"]:hover {
    background: #e85d2a !important;
}

/* ── inputs ── */
input, textarea, select {
    font-size: 16px !important;
    border-radius: 8px !important;
}

/* ── metric cards ── */
[data-testid="metric-container"] {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 12px 16px;
    border: 1px solid #e9ecef;
}

/* ── tabs ── */
.stTabs [data-baseweb="tab"] {
    font-size: 16px !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
}

/* ── cards ── */
.student-card {
    background: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 14px;
    padding: 16px;
    margin: 10px 0;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}

/* ── status pills ── */
.pill-green  { background:#d4edda; color:#155724; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:600; }
.pill-red    { background:#f8d7da; color:#721c24; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:600; }
.pill-orange { background:#fff3cd; color:#856404; padding:3px 10px; border-radius:20px; font-size:13px; font-weight:600; }

/* ── nav bar at top ── */
.nav-label { font-size:11px; font-weight:700; color:#6c757d; letter-spacing:1px; text-transform:uppercase; margin-bottom:4px; }

/* ── reduce page padding on mobile ── */
.block-container { padding: 1rem 0.75rem 3rem !important; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PERSISTENT STORAGE  via GitHub Gist
# ─────────────────────────────────────────────
# Add these to your Streamlit secrets (.streamlit/secrets.toml):
#   GITHUB_TOKEN = "ghp_xxxxxxxxxxxx"
#   GIST_ID      = "your_gist_id_here"
#
# How to set up (one-time):
#   1. Go to github.com → Settings → Developer settings → Personal access tokens → Tokens (classic)
#   2. Generate token with "gist" scope
#   3. Create a new Gist at gist.github.com with a file called tuition_data.json containing: {}
#   4. Copy the Gist ID from the URL
#   5. Add token + gist_id to your Streamlit app secrets

GIST_FILENAME = "tuition_data.json"

def _gist_headers():
    token = st.secrets.get("GITHUB_TOKEN", "")
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

def load_from_gist():
    """Load all app data from GitHub Gist."""
    gist_id = st.secrets.get("GIST_ID", "")
    if not gist_id:
        return {}
    try:
        r = requests.get(f"https://api.github.com/gists/{gist_id}", headers=_gist_headers(), timeout=8)
        if r.status_code == 200:
            content = r.json()["files"].get(GIST_FILENAME, {}).get("content", "{}")
            return json.loads(content)
    except Exception:
        pass
    return {}

def save_to_gist(data: dict):
    """Save all app data to GitHub Gist."""
    gist_id = st.secrets.get("GIST_ID", "")
    if not gist_id:
        st.warning("⚠️ Storage not configured. Data will be lost on refresh. See setup guide below.", icon="⚠️")
        return False
    try:
        payload = {"files": {GIST_FILENAME: {"content": json.dumps(data, indent=2)}}}
        r = requests.patch(f"https://api.github.com/gists/{gist_id}",
                           headers=_gist_headers(), json=payload, timeout=8)
        return r.status_code == 200
    except Exception as e:
        st.error(f"Save error: {e}")
        return False

def get_all_data():
    return {
        "students": st.session_state.students,
        "attendance": st.session_state.attendance,
        "reschedules": st.session_state.reschedules,
    }

def save_data():
    save_to_gist(get_all_data())


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "data_loaded" not in st.session_state:
    data = load_from_gist()
    st.session_state.students   = data.get("students",   [])
    st.session_state.attendance = data.get("attendance", [])
    st.session_state.reschedules= data.get("reschedules",[])
    st.session_state.data_loaded = True

if "page"          not in st.session_state: st.session_state.page = "home"
if "selected_days" not in st.session_state: st.session_state.selected_days = {}
if "edit_student"  not in st.session_state: st.session_state.edit_student = None
if "confirm_delete"not in st.session_state: st.session_state.confirm_delete = None


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
DAY_NAMES = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

def get_time_for_day(student, day_name):
    ts = student.get("time_slot", {})
    if isinstance(ts, dict):
        return ts.get(day_name, "—")
    return student.get("time_slot", "—")

def get_students_for_day(day_name, check_date=None):
    """Return students scheduled on day_name, accounting for reschedules."""
    base = []
    for s in st.session_state.students:
        ts = s.get("time_slot", {})
        days = list(ts.keys()) if isinstance(ts, dict) else s.get("days", [])
        if day_name in days:
            base.append(s)

    if check_date:
        date_str = str(check_date)
        rescheduled_away = {
            r["student_id"]
            for r in st.session_state.reschedules
            if r["original_date"] == date_str and r["status"] == "active"
        }
        base = [s for s in base if s["id"] not in rescheduled_away]

        extra_ids = {
            r["student_id"]
            for r in st.session_state.reschedules
            if r["new_date"] == date_str and r["status"] == "active"
        }
        for sid in extra_ids:
            s = next((x for x in st.session_state.students if x["id"] == sid), None)
            if s and s not in base:
                base.append(s)

    return base

def check_fee_status(student, month, year):
    return any(p["month"] == month and p["year"] == year for p in student.get("fees_paid", []))

def next_student_id():
    if not st.session_state.students:
        return 1
    return max(s["id"] for s in st.session_state.students) + 1

def go(page):
    st.session_state.page = page
    st.rerun()

def attendance_status(student_id, date_str):
    rec = next((a for a in st.session_state.attendance
                if a["student_id"] == student_id and a["date"] == date_str), None)
    return rec["status"] if rec else None

def mark_attendance(student, date_str, status):
    st.session_state.attendance = [
        a for a in st.session_state.attendance
        if not (a["student_id"] == student["id"] and a["date"] == date_str)
    ]
    st.session_state.attendance.append({
        "student_id":   student["id"],
        "student_name": student["name"],
        "date":         date_str,
        "status":       status,
        "timestamp":    datetime.now().isoformat()
    })
    save_data()
    st.rerun()


# ─────────────────────────────────────────────
# NAV BAR
# ─────────────────────────────────────────────
st.markdown("## 📚 Tuition Tracker")

pages = [
    ("🏠", "Today",     "home"),
    ("👥", "Students",  "students"),
    ("✅", "Attendance","attendance"),
    ("💰", "Fees",      "fees"),
    ("🔄", "Reschedule","reschedule"),
]

cols = st.columns(len(pages))
for col, (icon, label, pg) in zip(cols, pages):
    with col:
        btn_type = "primary" if st.session_state.page == pg else "secondary"
        if st.button(f"{icon}\n{label}", key=f"nav_{pg}", type=btn_type, use_container_width=True):
            st.session_state.page = pg
            st.rerun()

st.markdown("---")


# ════════════════════════════════════════════════════════════
# PAGE: HOME — Today's Classes
# ════════════════════════════════════════════════════════════
if st.session_state.page == "home":
    today_date = date.today()
    today_name = today_date.strftime("%A")

    st.subheader(f"📅 {today_date.strftime('%A, %d %B %Y')}")

    today_students = get_students_for_day(today_name, today_date)

    # ── summary metrics ──
    current_month = datetime.now().month
    current_year  = datetime.now().year

    m1, m2, m3 = st.columns(3)
    m1.metric("Today's Classes", len(today_students))
    m2.metric("Total Students",  len(st.session_state.students))
    fees_received = sum(
        float(s["monthly_fee"])
        for s in st.session_state.students
        if check_fee_status(s, current_month, current_year)
    )
    m3.metric("Fees This Month", f"₹{fees_received:,.0f}")

    st.markdown("---")

    if today_students:
        st.markdown(f"**{len(today_students)} class{'es' if len(today_students)>1 else ''} scheduled**")
        for student in today_students:
            reschedule = next(
                (r for r in st.session_state.reschedules
                 if r["student_id"] == student["id"]
                 and r["new_date"] == str(today_date)
                 and r["status"] == "active"), None
            )
            time_display = reschedule["new_time"] if reschedule else get_time_for_day(student, today_name)
            att_status = attendance_status(student["id"], str(today_date))

            with st.expander(f"👤 {student['name']} — {time_display}", expanded=True):
                c1, c2 = st.columns(2)
                c1.write(f"**Grade:** {student['grade']}")
                c1.write(f"**Subject:** {student['subject']}")
                c2.write(f"**Fee:** ₹{student['monthly_fee']}")
                if reschedule:
                    st.info(f"🔄 Rescheduled from {reschedule['original_date']}")

                if att_status == "present":
                    st.success("✅ Marked Present")
                elif att_status == "absent":
                    st.error("❌ Marked Absent")

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("✅ Present", key=f"hp_{student['id']}", use_container_width=True):
                        mark_attendance(student, str(today_date), "present")
                with bc2:
                    if st.button("❌ Absent", key=f"ha_{student['id']}", use_container_width=True):
                        mark_attendance(student, str(today_date), "absent")
    else:
        st.success("🎉 No classes today! Enjoy your day.")

    # ── upcoming week preview ──
    st.markdown("---")
    st.subheader("📆 Upcoming Week")
    for i in range(1, 7):
        upcoming = today_date + timedelta(days=i)
        up_name  = upcoming.strftime("%A")
        up_count = len(get_students_for_day(up_name, upcoming))
        if up_count:
            st.write(f"**{upcoming.strftime('%a %d %b')}** — {up_count} class{'es' if up_count>1 else ''}")


# ════════════════════════════════════════════════════════════
# PAGE: STUDENTS
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "students":
    st.subheader("👥 All Students")

    if st.button("➕ Add New Student", type="primary", use_container_width=True):
        st.session_state.edit_student  = None
        st.session_state.selected_days = {}
        st.session_state.page = "add_student"
        st.rerun()

    st.markdown("---")

    if not st.session_state.students:
        st.info("No students yet. Tap **Add New Student** to get started!")
    else:
        # search
        search = st.text_input("🔍 Search by name", placeholder="Type a name…")
        filtered = [
            s for s in st.session_state.students
            if search.lower() in s["name"].lower()
        ] if search else st.session_state.students

        st.write(f"Showing {len(filtered)} of {len(st.session_state.students)} students")

        for student in filtered:
            current_month = datetime.now().month
            current_year  = datetime.now().year
            fee_paid = check_fee_status(student, current_month, current_year)
            fee_badge = "✅ Paid" if fee_paid else "⏳ Pending"

            with st.expander(f"👤 {student['name']} | {student['grade']} | {fee_badge}"):
                c1, c2 = st.columns(2)
                c1.write(f"**Subject:** {student['subject']}")
                c1.write(f"**Fee:** ₹{student['monthly_fee']}/mo")
                if student.get("contact"):
                    c2.write(f"**Phone:** {student['contact']}")

                ts = student.get("time_slot", {})
                if isinstance(ts, dict) and ts:
                    c2.write("**Schedule:**")
                    for day, time in ts.items():
                        c2.caption(f"• {day}: {time}")

                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button("✏️ Edit", key=f"edit_{student['id']}", use_container_width=True):
                        st.session_state.edit_student  = student
                        st.session_state.selected_days = dict(student.get("time_slot", {}))
                        st.session_state.page = "add_student"
                        st.rerun()
                with bc2:
                    if st.button("🗑️ Delete", key=f"del_{student['id']}", use_container_width=True):
                        st.session_state.confirm_delete = student["id"]
                        st.rerun()

                # ── confirm delete (no nested buttons!) ──
                if st.session_state.confirm_delete == student["id"]:
                    st.warning(f"⚠️ Delete **{student['name']}**? This cannot be undone.")
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("✅ Yes, Delete", key=f"yes_del_{student['id']}", type="primary", use_container_width=True):
                            sid = student["id"]
                            st.session_state.students   = [s for s in st.session_state.students   if s["id"] != sid]
                            st.session_state.attendance = [a for a in st.session_state.attendance if a["student_id"] != sid]
                            st.session_state.reschedules= [r for r in st.session_state.reschedules if r["student_id"] != sid]
                            st.session_state.confirm_delete = None
                            save_data()
                            st.success("Student deleted.")
                            st.rerun()
                    with cc2:
                        if st.button("❌ Cancel", key=f"no_del_{student['id']}", use_container_width=True):
                            st.session_state.confirm_delete = None
                            st.rerun()


# ════════════════════════════════════════════════════════════
# PAGE: ADD / EDIT STUDENT
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "add_student":
    editing = st.session_state.edit_student is not None
    st.subheader("✏️ Edit Student" if editing else "➕ Add New Student")

    existing = st.session_state.edit_student or {}

    name    = st.text_input("Full Name *",       value=existing.get("name", ""),    placeholder="e.g. Rahul Sharma")
    grade   = st.text_input("Grade / Standard *", value=existing.get("grade", ""),   placeholder="e.g. 8th, 10th, JEE")
    subject = st.text_input("Subject *",          value=existing.get("subject", ""), placeholder="e.g. Mathematics, Science")
    fee     = st.number_input("Monthly Fee (₹) *", min_value=0, step=100,
                               value=int(existing.get("monthly_fee", 0)))
    contact = st.text_input("Phone Number (optional)", value=existing.get("contact", ""),
                             placeholder="e.g. 9876543210")

    st.markdown("---")
    st.markdown("**📅 Class Days & Times**")
    st.caption("Tap a day to select/deselect it, then enter the time.")

    for day in DAY_NAMES:
        is_sel = day in st.session_state.selected_days
        c1, c2 = st.columns([1, 2])
        with c1:
            label = f"{'✅' if is_sel else '⬜'} {day[:3]}"
            if st.button(label, key=f"day_{day}", use_container_width=True):
                if day in st.session_state.selected_days:
                    del st.session_state.selected_days[day]
                else:
                    st.session_state.selected_days[day] = ""
                st.rerun()
        with c2:
            if is_sel:
                t = st.text_input("Time", key=f"t_{day}",
                                  value=st.session_state.selected_days.get(day, ""),
                                  placeholder="4:00 PM – 5:00 PM",
                                  label_visibility="collapsed")
                st.session_state.selected_days[day] = t

    if st.session_state.selected_days:
        st.info(f"✅ {len(st.session_state.selected_days)} day(s) selected: " +
                ", ".join(st.session_state.selected_days.keys()))

    st.markdown("---")
    c1, c2 = st.columns(2)

    with c1:
        btn_label = "💾 Save Changes" if editing else "✅ Add Student"
        if st.button(btn_label, type="primary", use_container_width=True):
            schedule = {d: t for d, t in st.session_state.selected_days.items() if t.strip()}
            errors = []
            if not name.strip():   errors.append("Name is required")
            if not grade.strip():  errors.append("Grade is required")
            if not subject.strip():errors.append("Subject is required")
            if fee <= 0:           errors.append("Monthly fee must be > 0")
            if not schedule:       errors.append("Select at least one day with a time")

            if errors:
                for e in errors:
                    st.error(f"⚠️ {e}")
            else:
                if editing:
                    for s in st.session_state.students:
                        if s["id"] == existing["id"]:
                            s["name"]        = name.strip()
                            s["grade"]       = grade.strip()
                            s["subject"]     = subject.strip()
                            s["monthly_fee"] = fee
                            s["contact"]     = contact.strip()
                            s["time_slot"]   = schedule
                            break
                    msg = f"✅ {name} updated!"
                else:
                    st.session_state.students.append({
                        "id":          next_student_id(),
                        "name":        name.strip(),
                        "grade":       grade.strip(),
                        "subject":     subject.strip(),
                        "time_slot":   schedule,
                        "monthly_fee": fee,
                        "contact":     contact.strip(),
                        "fees_paid":   []
                    })
                    msg = f"✅ {name} added!"

                save_data()
                st.session_state.selected_days = {}
                st.session_state.edit_student  = None
                st.success(msg)
                st.balloons()
                st.session_state.page = "students"
                st.rerun()

    with c2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.selected_days = {}
            st.session_state.edit_student  = None
            st.session_state.page = "students"
            st.rerun()


# ════════════════════════════════════════════════════════════
# PAGE: ATTENDANCE
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "attendance":
    st.subheader("✅ Attendance")

    selected_date = st.date_input("📆 Select Date", value=date.today())
    day_name  = selected_date.strftime("%A")
    date_str  = str(selected_date)

    scheduled = get_students_for_day(day_name, selected_date)

    if not scheduled:
        st.info(f"No classes scheduled on {day_name}, {selected_date.strftime('%d %b %Y')}.")
    else:
        present_count = sum(1 for s in scheduled if attendance_status(s["id"], date_str) == "present")
        absent_count  = sum(1 for s in scheduled if attendance_status(s["id"], date_str) == "absent")
        unmarked      = len(scheduled) - present_count - absent_count

        m1, m2, m3 = st.columns(3)
        m1.metric("Total",    len(scheduled))
        m2.metric("Present",  present_count)
        m3.metric("Absent",   absent_count)

        if unmarked > 0:
            st.warning(f"⚠️ {unmarked} student(s) not yet marked")

        st.markdown("---")

        for student in scheduled:
            reschedule = next(
                (r for r in st.session_state.reschedules
                 if r["student_id"] == student["id"] and r["new_date"] == date_str and r["status"] == "active"),
                None
            )
            time_display = reschedule["new_time"] if reschedule else get_time_for_day(student, day_name)
            att = attendance_status(student["id"], date_str)

            with st.expander(
                f"{'✅' if att=='present' else '❌' if att=='absent' else '⏳'} "
                f"{student['name']} — {time_display}",
                expanded=(att is None)
            ):
                st.write(f"**Grade:** {student['grade']} | **Subject:** {student['subject']}")
                if reschedule:
                    st.info(f"🔄 Rescheduled from {reschedule['original_date']}")

                bc1, bc2 = st.columns(2)
                with bc1:
                    p_type = "primary" if att == "present" else "secondary"
                    if st.button("✅ Present", key=f"p_{student['id']}_{date_str}",
                                 type=p_type, use_container_width=True):
                        mark_attendance(student, date_str, "present")
                with bc2:
                    a_type = "primary" if att == "absent" else "secondary"
                    if st.button("❌ Absent", key=f"a_{student['id']}_{date_str}",
                                 type=a_type, use_container_width=True):
                        mark_attendance(student, date_str, "absent")

    # ── attendance history ──
    st.markdown("---")
    with st.expander("📊 View Attendance History"):
        if not st.session_state.students:
            st.info("No students yet.")
        else:
            sel_student = st.selectbox(
                "Select student",
                st.session_state.students,
                format_func=lambda s: s["name"]
            )
            recs = [a for a in st.session_state.attendance if a["student_id"] == sel_student["id"]]
            if recs:
                df = pd.DataFrame(recs)[["date", "status"]].sort_values("date", ascending=False)
                df.columns = ["Date", "Status"]
                df["Status"] = df["Status"].str.capitalize()
                st.dataframe(df, use_container_width=True, hide_index=True)
                total_p = len(df[df["Status"] == "Present"])
                total_a = len(df[df["Status"] == "Absent"])
                pct = int(total_p / len(df) * 100) if df.shape[0] > 0 else 0
                st.write(f"Attendance rate: **{pct}%** ({total_p} present, {total_a} absent)")
            else:
                st.info("No attendance records yet.")


# ════════════════════════════════════════════════════════════
# PAGE: FEES
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "fees":
    st.subheader("💰 Fee Management")

    if not st.session_state.students:
        st.info("No students added yet.")
    else:
        # month / year selector
        col_m, col_y = st.columns(2)
        with col_m:
            sel_month = st.selectbox("Month", range(1, 13),
                                     index=datetime.now().month - 1,
                                     format_func=lambda m: calendar.month_name[m])
        with col_y:
            cur_year = datetime.now().year
            sel_year = st.selectbox("Year", range(cur_year - 1, cur_year + 2), index=1)

        st.markdown(f"### {calendar.month_name[sel_month]} {sel_year}")

        total_exp = sum(float(s["monthly_fee"]) for s in st.session_state.students)
        total_rec = sum(
            float(s["monthly_fee"])
            for s in st.session_state.students
            if check_fee_status(s, sel_month, sel_year)
        )
        total_pen = total_exp - total_rec

        m1, m2, m3 = st.columns(3)
        m1.metric("Expected",  f"₹{total_exp:,.0f}")
        m2.metric("Received",  f"₹{total_rec:,.0f}")
        m3.metric("Pending",   f"₹{total_pen:,.0f}")

        st.markdown("---")

        # paid / unpaid tabs
        tab_pending, tab_paid = st.tabs(["⏳ Pending", "✅ Paid"])

        with tab_pending:
            unpaid = [s for s in st.session_state.students if not check_fee_status(s, sel_month, sel_year)]
            if not unpaid:
                st.success("🎉 All fees collected!")
            for student in unpaid:
                with st.expander(f"💸 {student['name']} — ₹{student['monthly_fee']}"):
                    st.write(f"**Grade:** {student['grade']} | **Subject:** {student['subject']}")
                    if student.get("contact"):
                        st.write(f"**Phone:** {student['contact']}")
                    if st.button(f"💰 Mark as Paid", key=f"pay_{student['id']}_{sel_month}_{sel_year}",
                                 type="primary", use_container_width=True):
                        student["fees_paid"].append({
                            "month":  sel_month,
                            "year":   sel_year,
                            "date":   datetime.now().isoformat(),
                            "amount": student["monthly_fee"]
                        })
                        save_data()
                        st.success(f"✅ ₹{student['monthly_fee']} received from {student['name']}")
                        st.rerun()

        with tab_paid:
            paid = [s for s in st.session_state.students if check_fee_status(s, sel_month, sel_year)]
            if not paid:
                st.info("No fees marked as paid yet.")
            for student in paid:
                payment = next(
                    (p for p in student.get("fees_paid", [])
                     if p["month"] == sel_month and p["year"] == sel_year), {}
                )
                paid_on = payment.get("date", "")[:10] if payment else ""
                with st.expander(f"✅ {student['name']} — ₹{student['monthly_fee']}"):
                    st.write(f"**Grade:** {student['grade']} | **Subject:** {student['subject']}")
                    if paid_on:
                        st.caption(f"Paid on: {paid_on}")
                    # allow un-marking
                    if st.button(f"↩️ Mark as Unpaid", key=f"unpay_{student['id']}_{sel_month}_{sel_year}",
                                 use_container_width=True):
                        student["fees_paid"] = [
                            p for p in student.get("fees_paid", [])
                            if not (p["month"] == sel_month and p["year"] == sel_year)
                        ]
                        save_data()
                        st.warning(f"↩️ Marked {student['name']} as unpaid")
                        st.rerun()


# ════════════════════════════════════════════════════════════
# PAGE: RESCHEDULE
# ════════════════════════════════════════════════════════════
elif st.session_state.page == "reschedule":
    st.subheader("🔄 Reschedule a Class")

    if not st.session_state.students:
        st.info("Add students first.")
        if st.button("➕ Add Student", use_container_width=True):
            go("add_student")
    else:
        tab_new, tab_history = st.tabs(["➕ New Reschedule", "📋 History"])

        with tab_new:
            student_idx = st.selectbox(
                "Select Student *",
                range(len(st.session_state.students)),
                format_func=lambda i: f"{st.session_state.students[i]['name']} — {st.session_state.students[i]['grade']}"
            )
            student = st.session_state.students[student_idx]

            ts = student.get("time_slot", {})
            if isinstance(ts, dict) and ts:
                st.info("📅 Regular Schedule: " + "  |  ".join(f"{d}: {t}" for d, t in ts.items()))

            original_date = st.date_input("📅 Original Class Date *", value=date.today())
            new_date      = st.date_input("📅 New Class Date *",      value=date.today() + timedelta(days=1))
            new_time      = st.text_input("⏰ New Time (leave blank to keep original)",
                                          placeholder="e.g. 5:00 PM – 6:00 PM")
            reason        = st.text_input("📝 Reason (optional)", placeholder="Holiday, sick, etc.")

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ Confirm Reschedule", type="primary", use_container_width=True):
                    if original_date == new_date:
                        st.error("Original and new dates must be different.")
                    else:
                        orig_day_name  = original_date.strftime("%A")
                        default_time   = get_time_for_day(student, orig_day_name)
                        st.session_state.reschedules.append({
                            "id":            next_student_id() + len(st.session_state.reschedules),
                            "student_id":    student["id"],
                            "student_name":  student["name"],
                            "original_date": str(original_date),
                            "new_date":      str(new_date),
                            "new_time":      new_time.strip() if new_time.strip() else default_time,
                            "reason":        reason,
                            "status":        "active",
                            "created_at":    datetime.now().isoformat()
                        })
                        save_data()
                        st.success(f"✅ {student['name']}'s class rescheduled to {new_date.strftime('%d %b %Y')}!")
                        st.balloons()
            with c2:
                if st.button("❌ Cancel", use_container_width=True):
                    go("home")

        with tab_history:
            active = [r for r in st.session_state.reschedules if r["status"] == "active"]
            if not active:
                st.info("No active reschedules.")
            else:
                for r in sorted(active, key=lambda x: x["new_date"]):
                    with st.expander(f"🔄 {r['student_name']} → {r['new_date']}"):
                        st.write(f"**Original:** {r['original_date']}")
                        st.write(f"**New Date:** {r['new_date']} at {r['new_time']}")
                        if r.get("reason"):
                            st.write(f"**Reason:** {r['reason']}")
                        if st.button("🗑️ Cancel Reschedule", key=f"cancel_r_{r['id']}", use_container_width=True):
                            r["status"] = "cancelled"
                            save_data()
                            st.success("Reschedule cancelled.")
                            st.rerun()


# ════════════════════════════════════════════════════════════
# SETUP GUIDE (shown when secrets not configured)
# ════════════════════════════════════════════════════════════
if not st.secrets.get("GIST_ID"):
    with st.expander("⚙️ One-Time Setup: Enable Persistent Storage", expanded=False):
        st.warning("Data is NOT being saved permanently yet. Follow these steps once:")
        st.markdown("""
**Step 1 — Create a GitHub Gist**
1. Go to [gist.github.com](https://gist.github.com)
2. Create a new **secret** gist
3. Filename: `tuition_data.json`
4. Content: `{}`
5. Click **Create secret gist**
6. Copy the **Gist ID** from the URL (the long string after your username)

**Step 2 — Create a GitHub Token**
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. Give it a name, select the **gist** scope only
4. Copy the generated token

**Step 3 — Add Secrets to Streamlit**
1. Go to your app on [share.streamlit.io](https://share.streamlit.io)
2. Click ⋮ → **Settings** → **Secrets**
3. Add:
```toml
GITHUB_TOKEN = "ghp_your_token_here"
GIST_ID      = "your_gist_id_here"
```
4. Click **Save** and restart the app

That's it! All data will now persist forever. ✅
        """)

# ── footer ──
st.markdown("---")
st.caption("Made with ❤️ for Mom  •  Data saves automatically")
