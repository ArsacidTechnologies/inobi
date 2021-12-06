import smtplib
from email.mime.text import MIMEText


from .configs import (
    SMTP_LOGIN,
    SMTP_SERVER
)


def send_email(to_address: iter, subject: str, message: str,
               username=SMTP_LOGIN[0], password=SMTP_LOGIN[1],
               from_address=None, smtp=SMTP_SERVER):

    if from_address is None:
        from_address = username

    server = smtplib.SMTP_SSL(smtp)
    o = server.ehlo()
    # print(o)
    # o = server.starttls()
    # print(o)
    server.login(username, password)
    # print(o)
    if not isinstance(to_address, (list, tuple, set)):
        msg = MIMEText(message)
        msg['From'] = from_address
        msg['TO'] = to_address
        msg['Subject'] = subject
        o = server.send_message(msg)
    else:
        for email in to_address:
            msg = MIMEText(message)
            msg['From'] = from_address
            msg['TO'] = email
            msg['Subject'] = subject
            o = server.send_message(msg)
    # print(o)
    o = server.quit()
    # print(o)
