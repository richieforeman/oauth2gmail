__author__ = 'Richie Foreman <richie.foreman@gmail.com>'

import httplib2
import imaplib
import email
from time import sleep
from oauth2client.client import AccessTokenRefreshError
import random
import smtplib
import base64
import re

IMAP_HOST = "imap.gmail.com"
SMTP_HOST = "smtp.gmail.com"

SMTP_PORT = smtplib.SMTP_SSL_PORT
IMAP_PORT = imaplib.IMAP4_SSL_PORT

http = httplib2.Http()

class GMailOAuth2Mixin(object):
    _credentials = None
    _username = None

    @staticmethod
    def refresh_credentials(credentials):
        authorized_http = credentials.authorize(http)
        for n in range(5):
            try:
                credentials.refresh(authorized_http)
                break
            except AccessTokenRefreshError:
                sleep((2 ** n) + random.randint(0, 1000) / 1000)
        return credentials

    @staticmethod
    def generate_xoauth2_string(username, access_token):
        return 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)

    def _get_oauth_string(self, username, credentials):
        if credentials.access_token_expired or credentials.access_token is None:
            credentials = self.refresh_credentials(credentials)

        self._credentials = credentials
        self._username = username

        auth_string = self.generate_xoauth2_string(username=username,
                                                   access_token=credentials.access_token)
        return auth_string

class GMail_SMTP(smtplib.SMTP, GMailOAuth2Mixin):
    def __init__(self, host=SMTP_HOST, port=SMTP_PORT, **kwargs):
        smtplib.SMTP.__init__(self, host, port, **kwargs)

    def login_oauth2(self, username, credentials):
        auth_string = self._get_oauth_string(username, credentials)
        self.docmd("AUTH", "XOAUTH2 %s" % base64.b64encode(auth_string))

class GMail_IMAP(imaplib.IMAP4_SSL, GMailOAuth2Mixin):
    def __init__(self, host=IMAP_HOST, port=IMAP_PORT, **kwargs):
        imaplib.IMAP4_SSL.__init__(self, host, port, **kwargs)

    def login_oauth2(self, username, credentials):
        auth_string = self._get_oauth_string(username, credentials)
        self.authenticate("XOAUTH2", lambda x: auth_string)

    def search_gm_msgid(self, msgid):
        '''
        Perform a search on X-GM-MSGID.  Designed to be similar to imap.search()
        '''
        return self.uid("SEARCH", "X-GM-MSGID", msgid)

    def fetch_gm_msgid(self, msgid, message_parts):
        '''
        Fetch a message on X-GM-MSGID.  Designed to be similar to imap.fetch()
        '''
        status, uids = self.search_gm_msgid(msgid)
        uids = uids[0].split(" ")

        return self.fetch(uids[0], message_parts=message_parts)

    def fetch_gm_msgid_message(self, msgid):
        status, uids = self.search_gm_msgid(msgid)

        uids = uids[0].split(" ")

        return self._fetch_message(uids[0])

    def _fetch_message(self, uid):
        '''
        This is a special method that takes care of fetching a message body into an email.Message object

        '''
        parts = ["X-GM-MSGID", "X-GM-THRID", "RFC822"]
        message_parts="(%s)" % " ".join(parts)

        mstatus, message_data = self.uid("fetch", uid, message_parts)
        extra_data = message_data[0][0]

        data = {}
        for p in parts:
            data[p] = re.search("%s\s([^\s]+)" % p, extra_data).group(1)
        data["uid"] = uid

        message = email.message_from_string(message_data[0][1])

        return (data, message)

    def gmsearch(self, query="in:anywhere", folder="[Gmail]/All Mail"):
        '''
        Perform a search with GMail using X-GM-RAW.

        This method is designed to behave like IMAP4.search().
        '''

        if folder:
            self.select(folder)

        return self.uid('SEARCH', "X-GM-RAW", query)

    def gmsearch_messages(self, query="in:anywhere", folder="[Gmail]/All Mail"):
        '''
        Perform a search with GMail, and yield a tuple (metadata dict, email.Message)
        '''
        status, uids = self.gmsearch(query, folder)
        print uids[0]
        uids = uids[0].split(" ")
        for uid in uids:
            #TODO: This is a great place to implement some nice error catching when Google decides to throw up errors.
            yield self._fetch_message(uid)