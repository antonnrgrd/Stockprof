# Import smtplib for the actual sending function
import smtplib

# Import the email modules we'll need
from email.message import EmailMessage


msg = EmailMessage()


# me == the sender's email address
# you == the recipient's email address
msg['Subject'] = f'nahhh bra'
msg['From'] = "antonnrgrd@hotmail.com"
msg['To'] = "antonnrgrd@hotmail.com"

# Send the message via our own SMTP server.
s = smtplib.SMTP('localhost')
s.send_message(msg)
s.quit()