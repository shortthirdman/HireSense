import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Content

class SendGridService:
    def __init__(self):
        self.sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        self.from_email = os.getenv('FROM_EMAIL')
        self.from_name = os.getenv('MAIL_FROM_NAME')
    def send_rejection_email(self, to_email, name):
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject='Application Status Update',
            plain_text_content=f"""
            Dear {name},
            Thank you for your interest in our company. After careful consideration, 
            we regret to inform you that we will not be moving forward with your 
            application at this time. We appreciate your time and effort in applying.
            Best regards,
            Recruitment Team
            """
        )
        try:
            response = self.sg.send(message)
            return response.status_code
        except Exception as e:
            print(f"Failed to send rejection email: {str(e)}")
            return False
    def forward_successful_applicant(self, to_email, applicant_data, assessment):
        html_content = f"""
        <p>Name: {applicant_data['name']}</p>
        <p>Email: {applicant_data['email']}</p>
        <p>Resume Path: <a href="{applicant_data['resume_path']}">View Resume</a></p>
        <p>Assessment:</p>
        <p>{assessment}</p>
        """
        plain_content = f"""
        Name: {applicant_data['name']}
        Email: {applicant_data['email']}
        Resume Path: {applicant_data['resume_path']}
        Assessment:
        {assessment}
        """
        message = Mail(
            from_email=(self.from_email, self.from_name),
            to_emails=to_email,
            subject=f"Successful Applicant: {applicant_data['name']}",
            plain_text_content=plain_content,
            html_content=html_content
        )
        try:
            response = self.sg.send(message)
            return response.status_code
        except Exception as e:
            print(f"Failed to send successful applicant email: {str(e)}")
            return False