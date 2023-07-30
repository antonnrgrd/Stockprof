import pandas as pd
import smtplib
import os
import json
# Import the email modules we'll need
from email.message import EmailMessage




# Send the message via our own SMTP server.

class StockMailer:
    def __init__(self):
        self.mail_text = ["Current status of watched items"]
    def ge_mailer_prepare_mailtext(self, ge_status):
        for updated_item in ge_status.formatted_info:
            self.mail_text.append[updated_item]
        self.mail_text.append(["The following items are changing rapidly in price"])
        for rapidly_changing_item in ge_status.notable_events:
            self.mail_text.append(rapidly_changing_item)
    def ge_mailer_mail_update(self):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        with open("{home}/stockscraper_config/meta_data.json".format(home=userhome), 'r') as f:
            data = json.load(f)
            self.ge_mailer_prepare_mailtext()
            msg = EmailMessage()
            msg['Subject'] = "Report on portfolio dated"
            msg['From'] = "StockProfiler"
            msg['To'] = data["email"]
            msg.set_content(self.mail_text)
            s = smtplib.SMTP('localhost')
            s.send_message(msg)
            s.quit()