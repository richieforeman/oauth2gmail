__author__ = 'Richie'

import unittest
from oauth2gmail import GMail_IMAP, GMail_SMTP
from oauth2client.client import SignedJwtAssertionCredentials, OAuth2WebServerFlow, flow_from_clientsecrets
from oauth2client.tools import run
from oauth2client.file import Storage
import os
import httplib2
import datetime
import email
httplib2.debuglevel = 4

BASEDIR = os.path.dirname(__file__)
PRIVATE_KEY = BASEDIR + "/privatekey.p12"
SERVICE_ACCOUNT_EMAIL = "497989677686@developer.gserviceaccount.com"
SCOPES = ["https://mail.google.com/"]

USERNAME = "richie@richieforeman.com"

class Test_SMTP_OAuth2(unittest.TestCase):
    def test_smtp_JWTserviceAccount(self):

        f = file(PRIVATE_KEY, 'rb')
        key = f.read()
        f.close()

        credentials = SignedJwtAssertionCredentials(service_account_name=SERVICE_ACCOUNT_EMAIL,
                                                    private_key=key,
                                                    scope=" ".join(SCOPES),
                                                    prn=USERNAME)

        smtp = GMail_SMTP()
        smtp.login_oauth2(USERNAME, credentials=credentials)

class Test_IMAP_OAuth2JWT(unittest.TestCase):
    def test_JWTServiceAccount(self):
        f = file(PRIVATE_KEY, 'rb')
        key = f.read()
        f.close()

        credentials = SignedJwtAssertionCredentials(service_account_name=SERVICE_ACCOUNT_EMAIL,
                                                    private_key=key,
                                                    scope=" ".join(SCOPES),
                                                    prn=USERNAME)

        imap = GMail_IMAP()
        imap.login_oauth2(USERNAME, credentials=credentials)

        imap.select("INBOX")

class Test_IMAP_OAuth2(unittest.TestCase):
    credentials = None
    imap = None


    def setUp(self):
        self.flow = flow_from_clientsecrets(filename=BASEDIR + "/client_secrets.json",
                                            scope=" ".join(SCOPES))

        storage = Storage("auth_secrets.dat")
        credentials = storage.get()
        if credentials is None or credentials.invalid:
            credentials = run(self.flow, storage)
        self.credentials = credentials

        imap = GMail_IMAP()
        imap.debug = 4
        imap.login_oauth2(USERNAME, credentials=self.credentials)
        imap.select("INBOX")
        self.imap = imap

    def test_gmsearch(self):
        status, data = self.imap.gmsearch("in:anywhere")

        self.assertEqual(status, "OK")
        # we should be able to parse a bunch of uids here.
        uids = data[0].split(" ")
        self.assertGreater(len(uids), 1)

    def test_gmsearch_messages(self):

        for data, message in self.imap.gmsearch_messages("in:anywhere"):
            # we should get a dictionary
            self.assertIsInstance(data, dict)
            # ... with a bunch of fields
            self.assertTrue(data.has_key("X-GM-MSGID"))
            self.assertTrue(data.has_key("X-GM-THRID"))
            self.assertTrue(data.has_key("uid"))
            # .. and a message object.
            self.assertTrue(message.has_key("From"))
            break

    def test_oauth2_token(self):
        username = "richie@richieforeman.com"
        access_token = "hahah"
        auth_string = GMail_IMAP.generate_xoauth2_string(username, access_token)
        self.assertEqual(auth_string, 'user=%s\1auth=Bearer %s\1\1' % (username, access_token))

    def test_imap_noaccesstoken(self):
        # the library should detect the lack of access token, and use the refresh token to go get a new one.
        self.credentials.access_token = None

        imap = GMail_IMAP()
        imap.debug = 4
        imap.login_oauth2(USERNAME, credentials=self.credentials)
        imap.select("INBOX")

    def test_imap_search_gm_msgid(self):

        # fetch a random sample message.
        message_data = None
        message = None
        for data, email in self.imap.gmsearch_messages():
            message_data = data
            message = email
            break

        # try to cash in the X-GM-MSGID
        status, data = self.imap.search_gm_msgid(message_data["X-GM-MSGID"])
        self.assertEqual(status, "OK")

    def test_imap_fetch_gm_msgid(self):

        # fetch a random sample message.
        message_data = None
        message = None
        for data, email in self.imap.gmsearch_messages():
            message_data = data
            message = email
            break

        status, data = self.imap.fetch_gm_msgid(message_data["X-GM-MSGID"], "(UID)")
        self.assertEqual(status, "OK")
    def test_imap_fetch_gm_msgid_message(self):

        # fetch a random sample message.
        message_data = None
        message = None
        for data, email in self.imap.gmsearch_messages():
            message_data = data
            message = email
            break

        data, email = self.imap.fetch_gm_msgid_message(message_data["X-GM-MSGID"])

        # should be the same thing.
        self.assertEqual(data, message_data)

    def test_imap_fromexpiredclientsecrets(self):

        # fake an expired token
        self.credentials.token_expiry = datetime.datetime(2012, 2, 10, 20, 59, 34)

        old_access_token = self.credentials.access_token

        imap = GMail_IMAP()
        imap.debug = 4
        imap.login_oauth2(USERNAME, credentials=self.credentials)
        imap.select("INBOX")

        self.assertNotEqual(old_access_token, imap._credentials.access_token, "We should have a new AccessToken")

    def test_imap_freshtoken(self):
        storage = Storage("null.dat")
        credentials = run(self.flow, storage)

        os.unlink("null.dat")

        imap = GMail_IMAP()
        imap.login_oauth2(USERNAME, credentials=credentials)
        imap.select("INBOX")


if __name__ == '__main__':
    unittest.main()
