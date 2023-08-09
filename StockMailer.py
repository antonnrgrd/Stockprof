# Import the following module
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
import smtplib
import os
import json



# Send the message via our own SMTP server.

class StockMailer:
    def __init__(self):
        self.mail_text = ["Current status of watched stocks"]
    def stock_mailer_prepare_mailtext(self, stock_status):
        for updated_item in stock_status.formatted_info:
            self.mail_text.append(updated_item)
        self.mail_text.append("The following items are changing rapidly in price \n ")
        for rapidly_changing_item in stock_status.notable_events:
            self.mail_text.append(rapidly_changing_item)
    def stock_mailer_setup_msg(subject="Python Notification", text="placeholder text", img=None,attachment=None):
        # build message contents
        msg = MIMEMultipart()
        # Add Subject
        msg['Subject'] = subject            
        # Add text contents
        msg.attach(MIMEText(text))      
        # Check if we have anything
        # given in the img parameter
        if img is not None:           
            # Check whether we have the lists of images or not!
            if type(img) is not list:                
                  # if it isn't a list, make it one
                img = [img]      
            # Now iterate through our list
            for one_img in img:              
                  # read the image binary data
                img_data = open(one_img, 'rb').read()  
                # Attach the image data to MIMEMultipart
                # using MIMEImage, we add the given filename use os.basename
                msg.attach(MIMEImage(img_data,
                                     name=os.path.basename(one_img)))     
        # We do the same for
        # attachments as we did for images
        if attachment is not None:              
            # Check whether we have the
            # lists of attachments or not!
            if type(attachment) is not list:                
                  # if it isn't a list, make it one
                attachment = [attachment]        
            for one_attachment in attachment:
      
                with open(one_attachment, 'rb') as f:
                    
                    # Read in the attachment
                    # using MIMEApplication
                    file = MIMEApplication(
                        f.read(),
                        name=os.path.basename(one_attachment)
                    )
                file['Content-Disposition'] = f'attachment;\
                filename="{os.path.basename(one_attachment)}"'
                  
                # At last, Add the attachment to our message object
                msg.attach(file)
        return msg
    def stock_mailer_mail_update(self,stock_status):
        userhome = os.path.expanduser('~')          
        user = os.path.split(userhome)[-1]
        with open("{home}/stockscraper_config/meta_data.json".format(home=userhome), 'r') as f:
            data = json.load(f)
            self.stock_mailer_prepare_mailtext(stock_status)
            msg = self.stock_mailer_setup_msg("Good!", self.mail_text)
            smtp = smtplib.SMTP('smtp.office365.com', 587)
            smtp.ehlo()
            smtp.starttls()
            smtp.login(data["email"], data["password"])
            # Make a list of emails, where you wanna send mail
            to = data["recipients"]
            # Provide some data to the sendmail function!
            smtp.sendmail(from_addr="antonnrgrd@hotmail.com",
                          to_addrs=to, msg=msg.as_string())        
             # Finally, don't forget to close the connection
            smtp.quit()