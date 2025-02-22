# standard library imports
import os
from datetime import datetime
from typing import Dict, List

# third-party imports
import jinja2
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, To

# local imports
from app.config.config import settings
from app.log_config import configure_logging
from app.templates.mail_messages import MailMessage

logger = configure_logging()

def _get_email_template(template_file):
    """
    Returns an email template file
    :param template_file: name of the template file.
    :return: email template file.
    """
    search_path = os.path.join(settings.BASE_DIR, "templates")

    template_loader = jinja2.FileSystemLoader(searchpath=search_path)
    template_environment = jinja2.Environment(loader=template_loader)

    return template_environment.get_template(template_file)


def _get_mail_body(
    copyright_year: int,
    file_name: str,
    given_names: str,
    organization_address: str = "Paris, France",
    organization_name: str = "Muchbetter AI",
    data: any = None,
):
    """
    This method builds a mail body as per the mailer object requirements. It takes the arguments below
    and leverages the provided email template files to render the respective html or text body files.

    :param action: Describes what action the email offers instructions for.
    :param action_tag: Identifies the organization that has sent the email by appending the organization name to
    the action parameter above. eg: Sample Organization: Reset your password.
    :param action_url: Provides a url which when appropriately accessed accomplishes the action described.
    :param copyright_year: Defines the year of the copyright for the software.
    :param file_name: Describes the email template file to use.
    :param given_names: The recipient's given names for mail personalization.
    :param mail_message: The instructions contained in the email.
    :param organization_address: A physical address for the organization.
    :param organization_name: The organization's name.
    :return:
    """
    template_file = file_name
    template = _get_email_template(template_file)
    mail_body = template.render(
        copyright_year=copyright_year,
        given_names=given_names,
        organization_address=organization_address,
        organization_name=organization_name,
        **data,
    )
    return mail_body


def send_email(
    recipients: List[Dict[str, str]],
    subject: str,
    text_body: str,
    html_body: str = None,
    sender: str = "noreply@muchbetter.ai",
):
    """
    Email a list of recipients.
    :param html_body:
    :param recipients:
    :param sender:
    :param subject:
    :param text_body:
    :return:
    """
    try:
        to_emails= [To(recipient["email"]) for recipient in recipients]
        message = Mail(
            from_email=sender,
            to_emails=to_emails,
            subject=subject,
            is_multiple=True,
            html_content=html_body
        )

        sendgrid_api_key = settings.SENDGRID_API_KEY
        sg = SendGridAPIClient(api_key=sendgrid_api_key)
        result = sg.send(message)
        logger.info(f"Email sent to {recipients} with result: {result}")

    except Exception as exception:
        logger.error(f"Failed to send email to {recipients} with error: {exception}")
    

class Mailer:
    def __init__(
        self,
        address: str,
        locale: str,
        organization_name: str,
        sender: str,
    ):
        lang = locale.lower().split("-")[0]

        self.organization_name = organization_name
        self.mail_message = MailMessage(lang, self.organization_name)
        self.mail_sender = sender
        self.organization_address = address
        self.organization_domain = settings.FRONTEND

    def send_template_email(
        self, mail_type: str, email: str, given_names: str, data: any
    ):
        ex_data = {}  # extra data to add (urls, translations ...)
        if mail_type == "user_activation":
            # action_tag, button_text, mail_message = self.mail_message.activate_user_mail_message()
            ex_data = self.mail_message.activate_user_mail_message()
            domain = self.organization_domain
            ex_data["action_url"] = domain + f"/auth/jwt/activate?token={data['token']}"
        elif mail_type == "reset_password":
            ex_data = self.mail_message.reset_user_password_mail_message()
            ex_data["action_url"] = (
                self.organization_domain + f"/auth/jwt/reset?token={data['token']}"
            )
        else:
            raise ValueError("Unsupported mial type.")
        copyright_year = datetime.now().year

        html_body = _get_mail_body(
            copyright_year=copyright_year,
            file_name=f"{data['template']}.html",
            given_names=given_names,
            organization_address=self.organization_address,
            organization_name=self.organization_name,
            data={**data, **ex_data},
        )

        text_body = _get_mail_body(
            copyright_year=copyright_year,
            file_name=f"{data['template']}.txt",
            given_names=given_names,
            organization_address=self.organization_address,
            organization_name=self.organization_name,
            data={**data, **ex_data},
        )

        send_email(
            html_body=html_body,
            recipients=[{"email": email, "name": given_names}],
            subject=ex_data["action_tag"],
            sender=self.mail_sender,
            text_body=text_body,
        )
