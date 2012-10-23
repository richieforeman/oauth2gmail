__author__ = 'Richie'

import unittest
import gmail_oauth2_imap as gmap
import os


class IMAP_OAuth2_Test(unittest.TestCase):
    def test_imap_oauth2_test(self):

        gmap.KEY = os.path.dirname(__file__) + "/.secret/privatekey.p12"
        gmap.SERVICE_ACCOUNT_EMAIL = "89576170682-1v4a6kh1l382akel7fs89an8q6kna61u@developer.gserviceaccount.com"
        gmap.IMAP_DEBUG_LEVEL = 4
        imap = gmap.get_imap_connection(prn="admin@onixdev1.com")

        imap.select("INBOX")

if __name__ == '__main__':
    unittest.main()
