from flask_mail import Mail, Message

mail = Mail()

def send_interview_email(app, tutor_email, tutor_name, subject,
                         interview_date, interview_time, zoom_link):

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

After the interview please prepare a 30-minute demo lesson teaching your selected subject:

{subject}

The recording should demonstrate your teaching style as if you were teaching a real student.

Kind regards,

MoreKnowledgeAcademy Recruitment Team

"""

        mail.send(msg)