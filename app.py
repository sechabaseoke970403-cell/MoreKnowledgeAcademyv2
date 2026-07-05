import secrets
import string
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for
from flask import send_from_directory
from database import create_tables, get_connection
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session
import os
from flask_mail import Mail
from services.email_service import mail, send_interview_email
from email_service import (
    mail,
    send_interview_email,
    send_activation_email,
    send_booking_email,
    send_new_booking_to_tutor
)
app = Flask(__name__)

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
import os

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True

app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_DEFAULT_SENDER")

app.secret_key = os.environ.get("SECRET_KEY")

UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs("uploads/photos", exist_ok=True)
os.makedirs("uploads/cvs", exist_ok=True)
os.makedirs("uploads/qualifications", exist_ok=True)
os.makedirs("uploads/ids", exist_ok=True)

def generate_activation_code():

    return ''.join(
        secrets.choice(string.digits)
        for _ in range(6)
    )

create_tables()


@app.route("/")
def home():
    return render_template("home.html")

@app.route("/apply", methods=["GET", "POST"])
def apply():

    if request.method == "POST":

        import uuid

        photo = request.files["photo"]
        cv = request.files["cv"]
        qualification_file = request.files["qualification_file"]
        id_document = request.files["id_document"]

        photo_name = f"{uuid.uuid4()}_{secure_filename(photo.filename)}"
        cv_name = f"{uuid.uuid4()}_{secure_filename(cv.filename)}"
        qualification_name = f"{uuid.uuid4()}_{secure_filename(qualification_file.filename)}"
        id_name = f"{uuid.uuid4()}_{secure_filename(id_document.filename)}"

        photo.save(f"uploads/photos/{photo_name}")
        cv.save(f"uploads/cvs/{cv_name}")
        qualification_file.save(f"uploads/qualifications/{qualification_name}")
        id_document.save(f"uploads/ids/{id_name}")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO tutor_applications(
            full_name,
            email,
            phone,
            province,
            city,
            subject,
            teaching_mode,
            qualification,
            experience,
            about,
            photo,
            cv,
            qualification_file,
            id_document
        )
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
         (
        request.form["full_name"],
        request.form["email"],
        request.form["phone"],
        request.form["province"],
        request.form["city"],
        request.form["subject"],
        request.form["teaching_mode"],
        request.form["qualification"],
        request.form["experience"],
        request.form["about"],
        photo_name,
        cv_name,
        qualification_name,
        id_name
    )
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("application_success"))

    return render_template("apply.html")
    
@app.route("/approve/<int:id>")
def approve(id):

    conn = get_connection()

    conn.execute("""

    UPDATE tutor_applications

    SET status='Approved'

    WHERE id=?

    """, (id,))

    conn.commit()

    conn.close()

    return redirect("/dashboard")    

@app.route("/application/<int:id>")
def application(id):

    if not session.get("admin"):

        return redirect("/admin")

    conn = get_connection()

    tutor = conn.execute(

        "SELECT * FROM tutor_applications WHERE id=?",

        (id,)

    ).fetchone()

    conn.close()

    return render_template(

        "application_details.html",

        tutor=tutor

    )

@app.route("/admin", methods=["GET","POST"])
def admin():

    if request.method == "POST":

        email = request.form["username"]
        password = request.form["password"]

        conn = get_connection()

        admin = conn.execute("""

        SELECT *

        FROM admins

        WHERE email=?

        """,(email,)).fetchone()

        conn.close()

        if admin:

            if check_password_hash(admin["password"], password):

                session["admin"] = admin["id"]

                return redirect("/dashboard")

        return "Invalid Login Details"

    return render_template("admin_login.html")

  

@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""

        INSERT INTO admins(

        full_name,
        email,
        password

        )

        VALUES(?,?,?)

        """,(

        full_name,
        email,
        password

        ))

        conn.commit()
        conn.close()

        return redirect("/admin")

    return render_template("admin_signup.html")

@app.route("/admin/logout")
def admin_logout():

    session.clear()

    return redirect("/admin")

@app.route("/dashboard")
def dashboard():

    if not session.get("admin"):

        return redirect("/admin")

    conn = get_connection()

    tutors = conn.execute(
        "SELECT * FROM tutor_applications ORDER BY created_at DESC"
    ).fetchall()

    pending = conn.execute(
        "SELECT COUNT(*) FROM tutor_applications WHERE status='Pending'"
    ).fetchone()[0]

    approved = conn.execute(
        "SELECT COUNT(*) FROM tutor_applications WHERE status='Approved'"
    ).fetchone()[0]

    interviews = conn.execute(
        "SELECT COUNT(*) FROM tutor_applications WHERE interview_status='Scheduled'"
    ).fetchone()[0]

    verified = conn.execute(
        "SELECT COUNT(*) FROM tutor_applications WHERE application_stage='Verified'"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "admin_dashboard.html",
        tutors=tutors,
        pending=pending,
        approved=approved,
        interviews=interviews,
        verified=verified
    )

@app.route("/reject/<int:id>")
def reject(id):

    if not session.get("admin"):

        return redirect("/admin")

    conn = get_connection()

    conn.execute("""

    UPDATE tutor_applications

    SET status='Rejected'

    WHERE id=?

    """,(id,))

    conn.commit()

    conn.close()

    return redirect("/dashboard")

@app.route("/schedule/<int:id>", methods=["GET", "POST"])
def schedule(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = get_connection()

    tutor = conn.execute(

        "SELECT * FROM tutor_applications WHERE id=?",

        (id,)

    ).fetchone()

    if request.method == "POST":

        interview_date = request.form["interview_date"]
        interview_time = request.form["interview_time"]
        zoom_link = request.form["zoom_link"]

        conn.execute("""

        UPDATE tutor_applications

        SET

        interview_date=?,
        interview_time=?,
        zoom_link=?,
        interview_status='Scheduled',
        application_stage='Interview Scheduled'

        WHERE id=?

        """,(

        interview_date,
        interview_time,
        zoom_link,
        id

        ))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    conn.close()

    return render_template(

        "schedule_interview.html",

        tutor=tutor

    )

    if not session.get("admin"):
        return redirect("/admin")

    conn = get_connection()
    
    tutor = conn.execute(

    "SELECT * FROM tutor_applications WHERE id=?",

    (id,)

    ).fetchone()

    if request.method == "POST":

        interview_date = request.form["interview_date"]
        interview_time = request.form["interview_time"]
        zoom_link = request.form["zoom_link"]

        conn.execute("""

        UPDATE tutor_applications

        SET

        interview_date=?,
        interview_time=?,
        zoom_link=?,
        interview_status='Scheduled'

        WHERE id=?

        """,(

        interview_date,
        interview_time,
        zoom_link,
        id

        ))

        conn.commit()
        
        send_interview_email(

    app,

    tutor["email"],

    tutor["full_name"],

    tutor["subject"],

    interview_date,

    interview_time,

    zoom_link

)
        
        conn.close()

        return redirect("/dashboard")

    tutor = conn.execute(

        "SELECT * FROM tutor_applications WHERE id=?",

        (id,)

    ).fetchone()

    conn.close()

    return render_template("schedule_interview.html", tutor=tutor)

    if not session.get("admin"):

        return redirect("/admin")

    return f"Schedule Interview for Tutor {id}"

@app.route("/application-success")
def application_success():

    return render_template("application_success.html")

@app.route("/uploads/<folder>/<filename>")
def uploaded_file(folder, filename):

    return send_from_directory(
        os.path.join("uploads", folder),
        filename
    )

@app.route("/request-demo/<int:id>")
def request_demo(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = get_connection()

    conn.execute("""

    UPDATE tutor_applications

    SET

    application_stage='Demo Lesson Requested'

    WHERE id=?

    """,(id,))

    conn.commit()
    conn.close()

    return redirect(f"/demo-upload/{id}")    

@app.route("/demo-upload/<int:id>", methods=["GET","POST"])
def demo_upload(id):

    conn = get_connection()

    tutor = conn.execute(

        "SELECT * FROM tutor_applications WHERE id=?",

        (id,)

    ).fetchone()

    if request.method == "POST":

        conn.execute("""

        UPDATE tutor_applications

        SET

        demo_video_link=?,
        application_stage='Demo Submitted'

        WHERE id=?

        """,(

        request.form["demo_video_link"],
        id

        ))

        conn.commit()

        conn.close()

        return "Demo Lesson Submitted Successfully."

    conn.close()

    return render_template(

        "demo_upload.html",

        tutor=tutor

    )

@app.route("/review-demo/<int:id>", methods=["GET","POST"])
def review_demo(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = get_connection()

    tutor = conn.execute(

        "SELECT * FROM tutor_applications WHERE id=?",

        (id,)

    ).fetchone()

    if request.method == "POST":

        conn.execute("""

        UPDATE tutor_applications

        SET

        demo_review=?,
        application_stage='Demo Approved'

        WHERE id=?

        """,(

        request.form["review"],
        id

        ))

        conn.commit()

        conn.close()

        return redirect("/dashboard")

    conn.close()

    return render_template(

        "review_demo.html",

        tutor=tutor

    )

@app.route("/create-tutor-account/<int:id>")
def create_tutor_account(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = get_connection()

    tutor = conn.execute(

        "SELECT * FROM tutor_applications WHERE id=?",

        (id,)

    ).fetchone()

    conn.execute("""

    INSERT INTO tutors(

    application_id,
    full_name,
    email,
    subject,
    teaching_mode

    )

    VALUES(?,?,?,?,?)

    """,(

    tutor["id"],
    tutor["full_name"],
    tutor["email"],
    tutor["subject"],
    tutor["teaching_mode"]

    ))

    conn.execute("""

    UPDATE tutor_applications

    SET

    account_created=1,
    application_stage='Account Created'

    WHERE id=?

    """,(id,))

    conn.commit()

    conn.close()

    return redirect("/dashboard")

@app.route("/create-password/<int:id>", methods=["GET","POST"])
def create_password(id):

    conn = get_connection()

    if request.method == "POST":

        password = generate_password_hash(

            request.form["password"]

        )

        conn.execute("""

        UPDATE tutors

        SET password=?

        WHERE id=?

        """,(password,id))

        conn.commit()

        conn.close()

        return redirect("/tutor-login")

    conn.close()

    return render_template(

        "tutor_create_password.html"

    )

@app.route("/tutor-login", methods=["GET","POST"])
def tutor_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()

        tutor = conn.execute("""

        SELECT *

        FROM tutors

        WHERE email=?

        """,(email,)).fetchone()

        conn.close()

        if tutor:

            if check_password_hash(
                tutor["password"],
                password
            ):

                session["tutor"] = tutor["id"]

                return redirect("/tutor-dashboard")

        return "Invalid Login"

    return render_template("tutor_login.html")

@app.route("/tutor-dashboard")
def tutor_dashboard():

    if not session.get("tutor"):

        return redirect("/tutor-login")

    conn = get_connection()

    tutor = conn.execute("""

    SELECT *

    FROM tutors

    WHERE id=?

    """,(session["tutor"],)).fetchone()

    conn.close()

    return render_template(
        "tutor_dashboard.html",
        tutor=tutor
    )

@app.route("/activate-tutor/<int:id>")
def activate_tutor(id):

    if not session.get("admin"):
        return redirect("/admin")

    conn = get_connection()

    tutor = conn.execute(
        "SELECT * FROM tutor_applications WHERE id=?",
        (id,)
    ).fetchone()

    if not tutor:
        conn.close()
        return "Tutor not found"

    code = generate_activation_code()
    token = secrets.token_urlsafe(32)

    conn.execute("""

    UPDATE tutor_applications

    SET
        activation_code=?,
        activation_token=?,
        activation_sent=1,
        activation_date=?,
        application_stage='Account Activation'

    WHERE id=?

    """, (

        code,
        token,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        id

    ))

    conn.execute("""

    UPDATE tutors

    SET verified=1

    WHERE application_id=?

    """, (id,))

    conn.commit()

    activation_link = url_for(
        "create_account",
        token=token,
        _external=True
    )

    send_activation_email(
        app,
        tutor["email"],
        tutor["full_name"],
        activation_link,
        code
    )

    conn.close()

    return redirect("/dashboard")

@app.route("/create-account/<token>", methods=["GET", "POST"])
def create_account(token):

    conn = get_connection()

    application = conn.execute("""

    SELECT *

    FROM tutor_applications

    WHERE activation_token=?

    """, (token,)).fetchone()

    if not application:
        conn.close()
        return "Invalid activation link."

    if request.method == "POST":

        password = generate_password_hash(
            request.form["password"]
        )

        conn.execute("""

        INSERT INTO tutors(

            application_id,
            full_name,
            email,
            password,
            phone,
            province,
            city,
            subject,
            teaching_mode,
            qualification,
            experience,
            profile_photo

        )

        VALUES(?,?,?,?,?,?,?,?,?,?,?,?)

        """, (

            application["id"],
            application["full_name"],
            application["email"],
            password,
            application["phone"],
            application["province"],
            application["city"],
            application["subject"],
            application["teaching_mode"],
            application["qualification"],
            application["experience"],
            application["photo"]

        ))

        conn.execute("""

        UPDATE tutor_applications

        SET
            activated=1,
            account_created=1

        WHERE id=?

        """, (application["id"],))

        conn.commit()
        conn.close()

        return redirect("/tutor-login")

    conn.close()

    return render_template(
        "create_account.html",
        tutor=application
    )

@app.route("/tutor-profile", methods=["GET", "POST"])
def tutor_profile():

    if "tutor" not in session:
        return redirect("/tutor-login")

    conn = get_connection()

    tutor = conn.execute(
        "SELECT * FROM tutors WHERE id=?",
        (session["tutor"],)
    ).fetchone()

    if request.method == "POST":

        bio = request.form.get("bio", "")
        province = request.form.get("province", "")
        city = request.form.get("city", "")
        teaching_mode = request.form.get("teaching_mode", "")
        hourly_rate = request.form.get("hourly_rate", "")

        photo_name = tutor["profile_photo"]

        photo = request.files.get("photo")

        if photo and photo.filename:

            filename = secure_filename(photo.filename)

            photo_name = filename

            photo.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    "photos",
                    filename
                )
            )

        conn.execute("""
            UPDATE tutors
            SET
                bio=?,
                province=?,
                city=?,
                teaching_mode=?,
                hourly_rate=?,
                profile_photo=?,
                profile_completed=1
            WHERE id=?
        """, (
            bio,
            province,
            city,
            teaching_mode,
            hourly_rate,
            photo_name,
            session["tutor"]
        ))

        conn.commit()
        conn.close()

        return redirect("/tutor-dashboard")

    conn.close()

    return render_template(
        "tutor_profile.html",
        tutor=tutor
    )
@app.route("/marketplace")
def marketplace():

    conn = get_connection()

    subject = request.args.get("subject", "")
    province = request.args.get("province", "")
    mode = request.args.get("mode", "")

    sql = """

    SELECT *

    FROM tutors

    WHERE

        profile_completed=1

        AND available=1

    """

    values = []

    if subject:

        sql += " AND subject LIKE ?"
        values.append(f"%{subject}%")

    if province:

        sql += " AND province LIKE ?"
        values.append(f"%{province}%")

    if mode:

        sql += " AND teaching_mode=?"
        values.append(mode)

    sql += " ORDER BY rating DESC"

    tutors = conn.execute(sql, values).fetchall()

    conn.close()

    return render_template(
        "marketplace.html",
        tutors=tutors
    )

    if "student" not in session:
        return redirect("/student-register")

    conn = get_connection()

    tutors = conn.execute("""

    SELECT *

    FROM tutors

    WHERE

        profile_completed = 1

        AND available = 1

    ORDER BY created_at DESC

    """).fetchall()

    conn.close()

    return render_template(
        "marketplace.html",
        tutors=tutors
    )

    if "student" not in session:
        return redirect("/student-register")

    conn = get_connection()

    tutors = conn.execute("""

    SELECT *

    FROM tutors

    WHERE

        profile_completed = 1

        AND available = 1

    ORDER BY created_at DESC

    """).fetchall()

    conn.close()

    return render_template(
        "marketplace.html",
        tutors=tutors
    )

    if "student" not in session:
        return redirect("/student-register")

    conn = get_connection()

    rows = conn.execute("""
        SELECT *
        FROM tutors
    """).fetchall()

    print("\n========== TUTORS IN DATABASE ==========")

    if len(rows) == 0:
        print("NO TUTORS FOUND")
    else:
        for row in rows:
            print(dict(row))

    print("========================================\n")

    tutors = conn.execute("""
        SELECT *
        FROM tutors
        ORDER BY created_at DESC
    """).fetchall()

    conn.close()

    return render_template(
        "marketplace.html",
        tutors=tutors
    )
@app.route("/student-signup", methods=["GET","POST"])
def student_signup():

    if request.method == "POST":

        conn = get_connection()

        conn.execute("""

        INSERT INTO students(

            full_name,
            email,
            phone,
            password

        )

        VALUES(?,?,?,?)

        """,(

            request.form["full_name"],
            request.form["email"],
            request.form["phone"],
            generate_password_hash(request.form["password"])

        ))

        conn.commit()
        conn.close()

        return redirect("/student-login")

    return render_template("student_signup.html")

@app.route("/student-login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()

        student = conn.execute(
            "SELECT * FROM students WHERE email=?",
            (email,)
        ).fetchone()

        conn.close()

        if student and check_password_hash(student["password"], password):

            session["student"] = student["id"]

            return redirect("/student-dashboard")

        return "Invalid email or password"

    return render_template("student_login.html")
@app.route("/student-dashboard")
def student_dashboard():

    if "student" not in session:
        return redirect("/student-login")

    conn = get_connection()

    student = conn.execute(
        "SELECT * FROM students WHERE id=?",
        (session["student"],)
    ).fetchone()

    conn.close()

    return render_template(
        "student_dashboard.html",
        student=student
    )
@app.route("/student-logout")
def student_logout():

    session.pop("student", None)

    return redirect("/")

from datetime import datetime

@app.route("/book/<int:tutor_id>", methods=["GET", "POST"])
def book_tutor(tutor_id):

    if "student" not in session:
        return redirect("/student-login")

    conn = get_connection()

    tutor = conn.execute(
        "SELECT * FROM tutors WHERE id=?",
        (tutor_id,)
    ).fetchone()

    student = conn.execute(
        "SELECT * FROM students WHERE id=?",
        (session["student"],)
    ).fetchone()

    availability = conn.execute("""

    SELECT *

    FROM tutor_availability

    WHERE tutor_id=?

    ORDER BY day,start_time

    """, (tutor_id,)).fetchall()

    if request.method == "POST":

        lesson_date = request.form["lesson_date"]
        lesson_time = request.form["lesson_time"]
        message = request.form["message"]

        day = datetime.strptime(
            lesson_date,
            "%Y-%m-%d"
        ).strftime("%A")

        slot = conn.execute("""

        SELECT *

        FROM tutor_availability

        WHERE tutor_id=?
        AND day=?
        AND start_time<=?
        AND end_time>=?

        """, (

            tutor_id,
            day,
            lesson_time,
            lesson_time

        )).fetchone()

        if not slot:

            conn.close()

            return render_template(
                "book_tutor.html",
                tutor=tutor,
                availability=availability,
                error="Tutor is not available at the selected date and time."
            )

        existing = conn.execute("""

        SELECT id

        FROM bookings

        WHERE tutor_id=?
        AND lesson_date=?
        AND lesson_time=?
        AND status!='Cancelled'

        """, (

            tutor_id,
            lesson_date,
            lesson_time

        )).fetchone()

        if existing:

            conn.close()

            return render_template(
                "book_tutor.html",
                tutor=tutor,
                availability=availability,
                error="This time has already been booked."
            )

        conn.execute("""

        INSERT INTO bookings(

            student_id,
            tutor_id,
            lesson_date,
            lesson_time,
            subject,
            message,
            amount

        )

        VALUES(?,?,?,?,?,?,?)

        """, (

            student["id"],
            tutor_id,
            lesson_date,
            lesson_time,
            tutor["subject"],
            message,
            tutor["hourly_rate"]

        ))

        conn.commit()

        booking_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.close()

        return redirect(f"/pay/{booking_id}")

    conn.close()

    return render_template(
        "book_tutor.html",
        tutor=tutor,
        availability=availability
    )
    
@app.route("/tutor-bookings")
def tutor_bookings():

    if "tutor" not in session:
        return redirect("/tutor-login")

    conn = get_connection()

    bookings = conn.execute("""

    SELECT

        bookings.*,

        students.full_name,
        students.email,
        students.phone

    FROM bookings

    JOIN students

    ON bookings.student_id = students.id

    WHERE bookings.tutor_id=?

    ORDER BY bookings.created_at DESC

    """,(session["tutor"],)).fetchall()

    conn.close()

    return render_template(

        "tutor_bookings.html",

        bookings=bookings

    )
@app.route("/accept-booking/<int:id>")
def accept_booking(id):

    if "tutor" not in session:
        return redirect("/tutor-login")

    conn = get_connection()

    conn.execute("""

    UPDATE bookings

    SET status='Accepted'

    WHERE id=?

    """,(id,))

    conn.commit()
    conn.close()

    return redirect("/tutor-bookings")
@app.route("/decline-booking/<int:id>")
def decline_booking(id):

    if "tutor" not in session:
        return redirect("/tutor-login")

    conn = get_connection()

    conn.execute("""

    UPDATE bookings

    SET status='Declined'

    WHERE id=?

    """,(id,))

    conn.commit()
    conn.close()

    return redirect("/tutor-bookings")
@app.route("/pay/<int:booking_id>")
def pay_booking(booking_id):

    if "student" not in session:
        return redirect("/student-login")

    conn = get_connection()

    booking = conn.execute("""

    SELECT

        bookings.*,

        tutors.full_name,

        tutors.hourly_rate

    FROM bookings

    JOIN tutors

    ON bookings.tutor_id=tutors.id

    WHERE bookings.id=?

    """,(booking_id,)).fetchone()

    conn.close()

    return render_template(
        "payfast.html",
        booking=booking
    )
    
@app.route("/payment-success")
def payment_success():

    booking_id = request.args.get("booking")

    if booking_id:

        conn = get_connection()

        conn.execute("""

        UPDATE bookings

        SET

            payment_status='Paid'

        WHERE id=?

        """,(booking_id,))

        booking = conn.execute("""

        SELECT

        bookings.*,

        students.full_name AS student_name,

        students.email AS student_email,

        tutors.full_name AS tutor_name,

        tutors.email AS tutor_email

        FROM bookings

        JOIN students ON bookings.student_id = students.id

        JOIN tutors ON bookings.tutor_id = tutors.id

        WHERE bookings.id=?

        """,(booking_id,)).fetchone()

        send_new_booking_to_tutor(

            app,

            booking["tutor_email"],

            booking["tutor_name"],

            booking["student_name"],

            booking["lesson_date"],

            booking["lesson_time"]

        )

        conn.commit()
        conn.close()

    return render_template("payment_success.html")
@app.route("/payment-cancel")
def payment_cancel():

    return render_template("payment_cancel.html")

@app.route("/tutor/<int:id>")
def tutor_details(id):

    conn = get_connection()

    tutor = conn.execute(
        "SELECT * FROM tutors WHERE id=?",
        (id,)
    ).fetchone()

    availability = conn.execute("""

    SELECT *

    FROM tutor_availability

    WHERE tutor_id=?

    ORDER BY day, start_time

    """, (id,)).fetchall()

    conn.close()

    return render_template(

        "tutor_details.html",

        tutor=tutor,

        availability=availability

    )


@app.route("/create-meeting/<int:id>", methods=["GET", "POST"])
def create_meeting(id):

    if "tutor" not in session:
        return redirect("/tutor-login")

    conn = get_connection()

    booking = conn.execute("""

    SELECT *

    FROM bookings

    WHERE id=?

    """,(id,)).fetchone()

    if request.method == "POST":

        conn.execute("""

        UPDATE bookings

        SET

            meeting_link=?,
            status='Ready'

        WHERE id=?

        """,(

            request.form["meeting_link"],
            id

        ))

        conn.commit()
        conn.close()

        return redirect("/tutor-bookings")

    conn.close()

    return render_template(
        "meeting_link.html",
        booking=booking
    )

@app.route("/tutor-earnings")
def tutor_earnings():

    if "tutor" not in session:
        return redirect("/tutor-login")

    conn = get_connection()

    bookings = conn.execute("""

    SELECT *

    FROM bookings

    WHERE

        tutor_id=?

        AND payment_status='Paid'

    ORDER BY created_at DESC

    """,(session["tutor"],)).fetchall()

    total = conn.execute("""

    SELECT

    COALESCE(SUM(lesson_price),0)

    FROM bookings

    WHERE

        tutor_id=?

        AND payment_status='Paid'

    """,(session["tutor"],)).fetchone()[0]

    conn.close()

    return render_template(

        "tutor_earnings.html",

        bookings=bookings,

        total=total

    )

@app.route("/admin-revenue")
def admin_revenue():

    if "admin" not in session:
        return redirect("/admin")

    conn = get_connection()

    total = conn.execute("""

    SELECT

    COALESCE(SUM(lesson_price),0)

    FROM bookings

    WHERE payment_status='Paid'

    """).fetchone()[0]

    bookings = conn.execute("""

    SELECT *

    FROM bookings

    WHERE payment_status='Paid'

    ORDER BY created_at DESC

    """).fetchall()

    conn.close()

    return render_template(

        "admin_revenue.html",

        total=total,

        bookings=bookings

    )

@app.route("/update-bookings")
def update_bookings():

    conn = get_connection()

    try:
        conn.execute("ALTER TABLE bookings ADD COLUMN meeting_link TEXT")
        conn.commit()
        message = "meeting_link column added successfully."

    except Exception as e:
        message = str(e)

    conn.close()

    return message

@app.route("/payfast-itn", methods=["POST"])
def payfast_itn():

    booking_id = request.form.get("custom_int1")
    payment_status = request.form.get("payment_status")

    if payment_status == "COMPLETE":

        conn = get_connection()

        conn.execute("""

        UPDATE bookings

        SET payment_status='Paid'

        WHERE id=?

        """,(booking_id,))

        conn.commit()
        conn.close()

    return "OK"
@app.route("/tutor-availability", methods=["GET","POST"])
def tutor_availability():

    if "tutor" not in session:
        return redirect("/tutor-login")

    conn = get_connection()

    if request.method == "POST":

        conn.execute("""

        INSERT INTO tutor_availability(

            tutor_id,
            day,
            start_time,
            end_time

        )

        VALUES(?,?,?,?)

        """,(

            session["tutor"],
            request.form["day"],
            request.form["start_time"],
            request.form["end_time"]

        ))

        conn.commit()

    availability = conn.execute("""

    SELECT *

    FROM tutor_availability

    WHERE tutor_id=?

    ORDER BY day

    """,(session["tutor"],)).fetchall()

    conn.close()

    return render_template(
        "tutor_availability.html",
        availability=availability
    )

@app.route("/my-lessons")
def my_lessons():

    if "student" not in session:
        return redirect("/student-login")

    conn = get_connection()

    bookings = conn.execute("""

    SELECT

        bookings.*,

        tutors.full_name,
        tutors.subject

    FROM bookings

    JOIN tutors

    ON bookings.tutor_id = tutors.id

    WHERE bookings.student_id=?

    ORDER BY bookings.created_at DESC

    """,(session["student"],)).fetchall()

    conn.close()

    return render_template(

        "my_lessons.html",

        bookings=bookings

    )

if __name__ == "__main__":
    app.run(debug=True)