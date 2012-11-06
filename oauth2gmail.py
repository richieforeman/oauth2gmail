__author__ = 'Richie Foreman <richie.foreman@gmail.com>'

import httplib2
import imaplib
import email
from time import sleep
import random
import smtplib
import base64

http = httplib2.Http()
IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

def generate_xoauth2_string(username, access_token):
    return 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)

def refresh_credentials(credentials):
    if not credentials.access_token:
        authorized_http = credentials.authorize(http)
    for n in range(5):
        try:
            credentials.refresh(authorized_http)
            break
        except:
            sleep((2 ** n) + random.randint(0, 1000) / 1000)
    return credentials

class GMail_SMTP(smtplib.SMTP):
    def __init__(self, host=SMTP_HOST, port=SMTP_PORT):
        smtplib.SMTP.__init__(self, host, port)

    def login_oauth2(self, username, credentials):
        credentials = refresh_credentials(credentials)
        auth_string = generate_xoauth2_string(username=username,
                                              access_token=credentials.access_token)
        self.docmd("AUTH", "XOAUTH2 %s" % base64.b64encode(auth_string))

class GMail_IMAP(imaplib.IMAP4_SSL):
    def __init__(self, host=IMAP_HOST, **kwargs):
        imaplib.IMAP4_SSL.__init__(self, host, **kwargs)

    def login_oauth2(self, username, credentials):

        credentials = refresh_credentials(credentials)

        auth_string = generate_xoauth2_string(username=username,
                                              access_token=credentials.access_token)

        self.authenticate("XOAUTH2", lambda x: auth_string)


    def search(self, query="in:anywhere", message_parts="(RFC822)"):
        '''
        Perform a search with GMail, and yield a list of email.Messages
        '''

        #select this, just incase the user forgets to.
        self.select("[Gmail]/All Mail")

        status, data = self.uid('SEARCH', "X-GM-RAW", query)
        if status == "OK":
            for uid in data[0].split(" "):
                message_text = self.uid("fetch", uid, message_parts)[1][0][1]
                yield email.message_from_string(message_text)
        else:
            raise Exception

    pass