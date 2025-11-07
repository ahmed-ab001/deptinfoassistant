from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import os

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET', 'change_this_secret')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ---------- MODELS ----------
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))

class HOD(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    achievements = db.Column(db.Text)

class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    designation = db.Column(db.String(100))
    achievements = db.Column(db.Text)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    roll_no = db.Column(db.String(20))
    achievements = db.Column(db.Text)

# Create DB and seed sample data if empty
with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        pw = bcrypt.generate_password_hash('admin123').decode('utf-8')
        db.session.add(Admin(username='admin', password=pw))
    if not HOD.query.first():
        db.session.add(HOD(name='Dr. Anjali Mehta', designation='Head of Department', achievements='Guided 10 PhD students; 50+ publications'))
    if not Staff.query.first():
        db.session.add(Staff(name='John Smith', designation='Assistant Professor', achievements='5 research papers; Member IEEE'))
        db.session.add(Staff(name='Sara Khan', designation='Lecturer', achievements='Organized national seminar on AI'))
    if not Student.query.first():
        db.session.add(Student(name='Ravi Kumar', roll_no='BT21CS001', achievements='Gold medal in coding fest'))
        db.session.add(Student(name='Priya Sharma', roll_no='BT21CS045', achievements='Volunteer of the year'))
    db.session.commit()

# ---------- ROUTES ----------
@app.route('/')
def home():
    hod = HOD.query.first()
    staff = Staff.query.all()
    return render_template('index.html', hod=hod, staff=staff)

@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_input = request.json.get('message', '').lower().strip()
    response = "Sorry, I didn't understand that. Try asking about 'HOD', 'staff', 'students', or mention a name."

    # ----- HOD -----
    if "hod" in user_input:
        hod = HOD.query.first()
        if hod:
            response = f"HOD: {hod.name} — {hod.designation}. Achievements: {hod.achievements}"
        else:
            response = "No HOD data available."

    # ----- All staff -----
    elif "staff" in user_input:
        staff = Staff.query.all()
        if staff:
            response = "Our staff members are: " + ", ".join([f"{s.name} ({s.designation})" for s in staff])
        else:
            response = "No staff records available."

    # ----- All students -----
    elif "student" in user_input or "students" in user_input:
        students = Student.query.all()
        if students:
            response = "Students: " + ", ".join([f"{st.name} (Roll: {st.roll_no})" for st in students])
        else:
            response = "No student records found."

    # ----- Specific staff or student -----
    else:
        matched_staff = None
        matched_student = None

        # Try to match staff name
        for s in Staff.query.all():
            if s.name.lower() in user_input:
                matched_staff = s
                break

        # Try to match student name
        for st in Student.query.all():
            if st.name.lower() in user_input:
                matched_student = st
                break

        if matched_staff:
            response = f"{matched_staff.name} — {matched_staff.designation}. Achievements: {matched_staff.achievements}"
        elif matched_student:
            response = f"Student: {matched_student.name} (Roll No: {matched_student.roll_no}). Achievements: {matched_student.achievements}"
        else:
            response = "I couldn’t find that name. Try the full name as in records."

            return jsonify({'response': response})

    if "hod" in user_input:
        hod = HOD.query.first()
        if hod:
            response = f"HOD: {hod.name} — {hod.designation}. Achievements: {hod.achievements}"
        else:
            response = "No HOD data available."
    elif "staff" in user_input:  
        staff = Staff.query.all()
        if staff:
            response = "Staff: " + ", ".join([f"{s.name} ({s.designation})" for s in staff])
        else:
            response = "No staff records."
    elif "student" in user_input or "students" in user_input:
        students = Student.query.all()
        if students:
            response = "Students: " + ", ".join([f"{st.name} (Roll: {st.roll_no})" for st in students])
        else:
            response = "No student records."
    elif "achievement" in user_input:
        parts = []
        for s in Staff.query.all():
            parts.append(f"{s.name}: {s.achievements}")
        hod = HOD.query.first()
        if hod:
            parts.insert(0, f"{hod.name} (HOD): {hod.achievements}")
        response = "\n".join(parts) if parts else "No achievements recorded."
    return jsonify({'response': response})

# ---------- ADMIN AUTH ----------
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = Admin.query.filter_by(username=request.form['username']).first()
        if user and bcrypt.check_password_hash(user.password, request.form['password']):
            session['admin'] = user.username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials.', 'danger')
    return render_template('admin_login.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    hod = HOD.query.first()
    staff = Staff.query.all()
    students = Student.query.all()
    return render_template('dashboard.html', hod=hod, staff=staff, students=students)

# ---------- CRUD ----------
@app.route('/add_staff', methods=['POST'])
def add_staff():
    if 'admin' in session:
        name = request.form.get('name')
        designation = request.form.get('designation')
        achievements = request.form.get('achievements')
        db.session.add(Staff(name=name, designation=designation, achievements=achievements))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit_staff/<int:sid>', methods=['GET', 'POST'])
def edit_staff(sid):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    s = Staff.query.get_or_404(sid)
    if request.method == 'POST':
        s.name = request.form.get('name')
        s.designation = request.form.get('designation')
        s.achievements = request.form.get('achievements')
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_staff.html', staff=s)

@app.route('/delete_staff/<int:sid>')
def delete_staff(sid):
    if 'admin' in session:
        s = Staff.query.get_or_404(sid)
        db.session.delete(s)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_hod', methods=['POST'])
def add_hod():
    if 'admin' in session:
        # Replace or create HOD
        HOD.query.delete()
        name = request.form.get('name')
        designation = request.form.get('designation')
        achievements = request.form.get('achievements')
        db.session.add(HOD(name=name, designation=designation, achievements=achievements))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'admin' in session:
        name = request.form.get('name')
        roll = request.form.get('roll_no')
        achievements = request.form.get('achievements')
        db.session.add(Student(name=name, roll_no=roll, achievements=achievements))
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/edit_student/<int:stid>', methods=['GET', 'POST'])
def edit_student(stid):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))
    st = Student.query.get_or_404(stid)
    if request.method == 'POST':
        st.name = request.form.get('name')
        st.roll_no = request.form.get('roll_no')
        st.achievements = request.form.get('achievements')
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_student.html', student=st)

@app.route('/delete_student/<int:stid>')
def delete_student(stid):
    if 'admin' in session:
        st = Student.query.get_or_404(stid)
        db.session.delete(st)
        db.session.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
