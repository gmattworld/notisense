import datetime
import os


def load_template(template_name: str) -> str:
    template_folder = os.path.join(os.path.dirname(__file__), "../templates")
    template_path = os.path.join(template_folder, template_name)
    with open(template_path, "r") as file:
        template_content = file.read()
    return template_content


def get_registration_template(first_name: str, code: str) -> str:
    template_content = load_template("registration.html")
    template_content = template_content.replace("{{FIRST_NAME}}", first_name)
    template_content = template_content.replace("{{TOKEN}}", code)
    template_content = template_content.replace("{{COPYRIGHT_YEAR}}", str(datetime.datetime.now().year))
    return template_content


def get_password_reset_template(first_name: str, code: str) -> str:
    template_content = load_template("reset_password.html")
    template_content = template_content.replace("{{FIRST_NAME}}", first_name)
    template_content = template_content.replace("{{TOKEN}}", code)
    template_content = template_content.replace("{{COPYRIGHT_YEAR}}", str(datetime.datetime.now().year))
    return template_content


def get_invitation_template(first_name: str, tenant_name: str, call_to_action_link: str) -> str:
    template_content = load_template("invitation.html")
    template_content = template_content.replace("{{FIRST_NAME}}", first_name)
    template_content = template_content.replace("{{TENANT_NAME}}", tenant_name)
    template_content = template_content.replace("{{CALL_TO_ACTION_LINK}}", call_to_action_link)
    template_content = template_content.replace("{{COPYRIGHT_YEAR}}", str(datetime.datetime.now().year))
    return template_content
