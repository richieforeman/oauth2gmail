__author__ = 'Richie'

import unittest
from oauth2gmail import GMail_IMAP, GMail_SMTP
from oauth2client.client import SignedJwtAssertionCredentials, OAuth2WebServerFlow, flow_from_clientsecrets
from oauth2client.tools import run
from oauth2client.file import Storage
import os

PRIVATE_KEY = os.path.dirname(__file__) + "/privatekey.p12"
SERVICE_ACCOUNT_EMAIL = "497989677686@developer.gserviceaccount.com"
SCOPES = ["https://mail.google.com/"]

CLIENT_ID_WEB = "497989677686-udv6eqr67p4iq606rn6ifjbh277g5aef.apps.googleusercontent.com"
CLIENT_SECRET_WEB = open("client_secret_web.txt").read().strip()

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



class Test_IMAP_OAuth2(unittest.TestCase):
    def test_imap_JWTserviceAccount(self):

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

    def test_imap_webServerFlow(self):
        flow = OAuth2WebServerFlow(client_id=CLIENT_ID_WEB,
                                   client_secret=CLIENT_SECRET_WEB,
                                   scope=" ".join(SCOPES))

        storage = Storage("auth.dat")
        credentials = run(flow, storage)
        credentials.authorize()

        imap = GMail_IMAP()
        imap.login_oauth2(USERNAME, credentials=credentials)
        imap.select("INBOX")

    def test_imap_fromclientsecrets(self):
        flow = flow_from_clientsecrets(filename="client_secrets.json",
                                       scope=" ".join(SCOPES))

        storage = Storage("auth_secrets.dat")
        credentials = run(flow, storage)

        imap = GMail_IMAP()
        imap.login_oauth2(USERNAME, credentials=credentials)
        imap.select("INBOX")




if __name__ == '__main__':
    unittest.main()
