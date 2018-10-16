import os
import logging
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart

import config

main_logger = logging.getLogger('email')


def send(to, subject, body, filename):
    if hasattr(config, 'gmail_user') and hasattr(config, 'gmail_pass'):

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = config.gmail_user
        msg['To'] = to

        text = MIMEText(body)
        msg.attach(text)

        if filename:
            with open(filename, 'rb') as img_f:
                image = MIMEImage(img_f.read(), name=os.path.basename('img.jpg'))
                msg.attach(image)

        try:
            # Allow access for less secure apps in your Google account, otherwise exception is thrown
            s = smtplib.SMTP('smtp.gmail.com', 587)
            s.ehlo()
            s.starttls()
            s.login(config.gmail_user, config.gmail_pass)
            s.sendmail(msg['From'], msg['To'], msg.as_string())
            s.quit()
        except:
            main_logger.error('failed to send mail to %s' % to)
            traceback.print_exc()
