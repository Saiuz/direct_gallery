import imaplib
import email
import os
import time
import datetime
from pprint import pprint

svdir = './mail'

IMAP4_ADDR = str(os.environ['IMAP4_ADDR'])
IMAP4_USER = str(os.environ['IMAP4_USER'])
IMAP4_PWD = str(os.environ['IMAP4_PWD'])

if len(IMAP4_ADDR) <= 0 or len(IMAP4_USER) <= 0 or len(IMAP4_PWD):
    print("Please set environment variables")
    exit(1)

def fetch_emails():
    mail=imaplib.IMAP4_SSL(IMAP4_ADDR)
    mail.login(IMAP4_USER,IMAP4_PWD)
    rv, data = mail.list()
    l = data[0].decode().split('"/"')
    rv, data = mail.select('"INBOX"')
    if rv=='OK':

        date = (datetime.date.today() - datetime.timedelta(1)).strftime("%d-%b-%Y")     # mails in recent one day
        result, msgs = mail.search(None, '(SENTSINCE {date})'.format(date=date))
        msgs = msgs[0].split()
        print(msgs)

        for emailid in msgs:
            resp, data = mail.fetch(emailid, "(RFC822)")
            email_body = data[0][1] 
            m = email.message_from_string(email_body.decode())


            if m.get_content_maintype() != 'multipart':
                continue

            for part in m.walk():
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue

                filename=part.get_filename()
                if filename is not None:
                    sv_path = os.path.join(svdir, filename)
                    if not os.path.isfile(sv_path):
                        print(sv_path)
                        fp = open(sv_path, 'wb')
                        fp.write(part.get_payload(decode=True))
                        fp.close()
        mail.close()
        print(str(time.time()) + str(": email fetched"))
    else:
        print('AUTH failed. exit(1)')
        exit(1)

while True:
    fetch_emails()
    time.sleep(60)