from flask_mail import Mail, Message


mail = Mail()


def send_interview_email(
    app,
    tutor_email,
    tutor_name,
    subject,
    interview_date,
    interview_time,
    zoom_link
):

    with app.app_context():

        msg = Message(
            subject="MoreKnowledgeAcademy Interview Invitation",
            recipients=[tutor_email]
        )

        msg.body = f"""
Dear {tutor_name},

Congratulations.

Your tutor application has progressed to the interview stage.

Interview Details

Date: {interview_date}

Time: {interview_time}

Zoom Link:
{zoom_link}

Please prepare a 30-minute demo lesson teaching:

{subject}

Regards,

MoreKnowledgeAcademy Recruitment Team
"""

        mail.send(msg)


def send_activation_email(
    app,
    tutor_email,
    tutor_name,
    activation_link,
    activation_code
):

    with app.app_context():

        msg = Message(
            subject="Activate Your MoreKnowledgeAcademy Tutor Account",
            recipients=[tutor_email]
        )

        msg.body = f"""
Dear {tutor_name},

Congratulations!

Your application has been approved.

Please activate your tutor account.

Activation Link

{activation_link}

Activation Code

{activation_code}

Use the activation code when creating your account.

Regards,

MoreKnowledgeAcademy Recruitment Team
"""

        mail.send(msg)
        
def send_booking_email(
    app,
    student_email,
    student_name,
    tutor_name,
    lesson_date,
    lesson_time
):

    with app.app_context():

        msg = Message(

            subject="Lesson Booking Confirmation",

            recipients=[student_email]

        )

        msg.body = f"""
Hello {student_name},

Your booking has been received successfully.

Tutor:
{tutor_name}

Lesson Date:
{lesson_date}

Lesson Time:
{lesson_time}

Please complete your payment to confirm your lesson.

Thank you.

MoreKnowledgeAcademy
"""

        mail.send(msg)        
        
def send_new_booking_to_tutor(

    app,

    tutor_email,

    tutor_name,

    student_name,

    lesson_date,

    lesson_time

):

    with app.app_context():

        msg = Message(

            subject="New Lesson Booking",

            recipients=[tutor_email]

        )

        msg.body = f"""
Hello {tutor_name},

You have received a new lesson booking.

Student:
{student_name}

Date:
{lesson_date}

Time:
{lesson_time}

Please log in to your tutor dashboard to accept the booking.

MoreKnowledgeAcademy
"""

        mail.send(msg)        