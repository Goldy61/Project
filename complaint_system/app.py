from flask import Flask, render_template, request, redirect, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from functools import wraps

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="complaint_db"
)
cursor = db.cursor()

# ---------------- EMAIL ----------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'yourprojectemail@gmail.com'
app.config['MAIL_PASSWORD'] = 'njwjpiuaaziqenox'
app.config['MAIL_DEFAULT_SENDER'] = 'yourprojectemail@gmail.com'
mail = Mail(app)

# ---------------- AUTH DECORATOR ----------------
def login_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated(*args, **kwargs):
            if 'role' not in session or session['role'] != role:
                return redirect('/')
            return fn(*args, **kwargs)
        return decorated
    return wrapper

# ---------------- LOGIN ----------------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['role'] = user[4]   # ⚠️ THIS INDEX IS IMPORTANT

            if session['role'] == 'user':
                return redirect('/user')
            elif session['role'] == 'admin':
                return redirect('/admin')
            elif session['role'] == 'staff':
                return redirect('/staff')

    return render_template("login.html")


# ---------------- REGISTER ----------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        hashed = generate_password_hash(request.form['password'])
        cursor.execute(
            "INSERT INTO users(username,password,email,role) VALUES(%s,%s,%s,%s)",
            (request.form['username'], hashed,
             request.form['email'], request.form['role'])
        )
        db.commit()
        return redirect('/')
    return render_template("register.html")

# ---------------- USER DASHBOARD ----------------
@app.route('/user')
@login_required('user')
def user_dashboard():
    cursor.execute("""
        SELECT id, category, description, status 
        FROM complaints WHERE user_id=%s
    """, (session['user_id'],))
    complaints = cursor.fetchall()
    return render_template("user_dashboard.html", complaints=complaints)

@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    cursor.execute(
        "INSERT INTO complaints(user_id, category, description, status) VALUES (%s,%s,%s,'Pending')",
        (session['user_id'], request.form['category'], request.form['description'])
    )
    db.commit()
    


    cursor.execute("SELECT email FROM users WHERE id=%s", (session['user_id'],))
    email = cursor.fetchone()[0]

    mail.send(Message(
        "Complaint Submitted",
        recipients=[email],
        body="Your complaint has been submitted successfully."
    ))
    return jsonify({"success": True})

# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin', methods=['GET','POST'])
@login_required('admin')
def admin_dashboard():
    if request.method == 'POST':
        cid = request.form['cid']
        staff_id = request.form['staff_id']
        cursor.execute(
            "UPDATE complaints SET staff_id=%s, status='In Progress' WHERE id=%s",
            (staff_id, cid)
        )
        db.commit()

        cursor.execute("SELECT email FROM users WHERE id=%s", (staff_id,))
        mail.send(Message(
            "New Complaint Assigned",
            recipients=[cursor.fetchone()[0]],
            body="A complaint has been assigned to you."
        ))

    cursor.execute("""
        SELECT c.id,c.category,c.description,c.status,u.username 
        FROM complaints c JOIN users u ON c.user_id=u.id
    """)
    complaints = cursor.fetchall()

    cursor.execute("SELECT id,username FROM users WHERE role='staff'")
    staff = cursor.fetchall()

    return render_template("admin_dashboard.html",
                           complaints=complaints, staff=staff)

@app.route('/admin_chart_data')
@login_required('admin')
def admin_chart_data():
    data = {}
    for s in ['Pending','In Progress','Resolved']:
        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status=%s", (s,))
        data[s] = cursor.fetchone()[0]
    return jsonify(data)

# ---------------- STAFF DASHBOARD ----------------
@app.route('/staff', methods=['GET','POST'])
@login_required('staff')
def staff_dashboard():
    if request.method == 'POST':
        cid = request.form['cid']
        cursor.execute("UPDATE complaints SET status='Resolved' WHERE id=%s", (cid,))
        db.commit()

        cursor.execute("""
            SELECT u.email FROM users u
            JOIN complaints c ON u.id=c.user_id WHERE c.id=%s
        """, (cid,))
        mail.send(Message(
            "Complaint Resolved",
            recipients=[cursor.fetchone()[0]],
            body="Your complaint has been resolved."
        ))

    cursor.execute("""
        SELECT id,category,description,status 
        FROM complaints WHERE staff_id=%s
    """, (session['user_id'],))
    complaints = cursor.fetchall()
    return render_template("staff_dashboard.html", complaints=complaints)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
