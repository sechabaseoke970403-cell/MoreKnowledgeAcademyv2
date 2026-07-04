import sqlite3
import os

DATABASE = "instance/database.db"


def get_connection():
    os.makedirs("instance", exist_ok=True)

    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row

    return connection


def create_tables():

    conn = get_connection()
    cursor = conn.cursor()

    # ======================================================
    # TUTOR APPLICATIONS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS tutor_applications(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,

        province TEXT NOT NULL,
        city TEXT NOT NULL,

        subject TEXT NOT NULL,
        teaching_mode TEXT NOT NULL,

        qualification TEXT NOT NULL,
        experience INTEGER,
        about TEXT,

        photo TEXT,
        cv TEXT,
        qualification_file TEXT,
        id_document TEXT,

        status TEXT DEFAULT 'Pending',

        application_stage TEXT DEFAULT 'Applied',

        interview_status TEXT DEFAULT 'Pending',
        interview_date TEXT,
        interview_time TEXT,
        zoom_link TEXT,

        invitation_sent INTEGER DEFAULT 0,

        demo_video_link TEXT,
        demo_review TEXT,

        activation_code TEXT,
        activation_token TEXT,
        activation_sent INTEGER DEFAULT 0,
        activation_date TEXT,

        activated INTEGER DEFAULT 0,
        account_created INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # ADMINS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS admins(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        full_name TEXT NOT NULL,

        email TEXT UNIQUE NOT NULL,

        password TEXT NOT NULL,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # ======================================================
    # TUTORS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS tutors(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        application_id INTEGER,

        full_name TEXT,
        email TEXT UNIQUE,
        password TEXT,

        phone TEXT,

        province TEXT,
        city TEXT,

        subject TEXT,
        teaching_mode TEXT,

        qualification TEXT,
        experience INTEGER,

        bio TEXT,

        hourly_rate REAL,

        profile_photo TEXT,

        verified INTEGER DEFAULT 0,

        profile_completed INTEGER DEFAULT 0,

        available INTEGER DEFAULT 1,

        rating REAL DEFAULT 0,

        total_reviews INTEGER DEFAULT 0,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

        FOREIGN KEY(application_id)
        REFERENCES tutor_applications(id)

    )

    """)

    # ======================================================
    # BOOKINGS
    # ======================================================
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS bookings(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    tutor_id INTEGER NOT NULL,

    student_id INTEGER NOT NULL,

    lesson_date TEXT,

    lesson_time TEXT,

    lesson_type TEXT,

    lesson_duration TEXT,

    lesson_price REAL,

    payment_status TEXT DEFAULT 'Pending',

    status TEXT DEFAULT 'Pending',

    meeting_link TEXT,

    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY(tutor_id) REFERENCES tutors(id),

    FOREIGN KEY(student_id) REFERENCES students(id)

)

""")

    cursor.execute("DROP TABLE IF EXISTS bookings")

    # ======================================================
    # REVIEWS
    # ======================================================

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS reviews(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        tutor_id INTEGER,

        student_name TEXT,

        rating INTEGER,

        review TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS students(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    full_name TEXT NOT NULL,

    email TEXT UNIQUE NOT NULL,

    phone TEXT,

    password TEXT NOT NULL,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)

""")
    cursor.execute("""

    CREATE TABLE IF NOT EXISTS bookings(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    student_id INTEGER,

    tutor_id INTEGER,

    lesson_date TEXT,

    lesson_time TEXT,

    subject TEXT,

    message TEXT,
     
    amount REAL DEFAULT 0, 
     
    status TEXT DEFAULT 'Pending',

    payment_status TEXT DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

)

""")    
    
    cursor.execute("""

CREATE TABLE IF NOT EXISTS tutor_availability(

    id INTEGER PRIMARY KEY AUTOINCREMENT,

    tutor_id INTEGER,

    day TEXT,

    start_time TEXT,

    end_time TEXT,

    FOREIGN KEY(tutor_id)
    REFERENCES tutors(id)

)

""")

    conn.commit()
    conn.close()
    
