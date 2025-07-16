import imaplib
import email
import csv
import getpass
from email.header import decode_header, make_header

# --- USER CONFIGURATION ---
IMAP_HOST     = 'imap.gmail.com'
EMAIL_ACCOUNT = input("Gmail address: ")
PASSWORD      = getpass.getpass("App password (or Gmail password if IMAP is enabled): ")

print("Connecting to IMAP server...")
imap = imaplib.IMAP4_SSL(IMAP_HOST)
imap.login(EMAIL_ACCOUNT, PASSWORD)
imap.select('INBOX', readonly=True)
print("Logged in. INBOX selected.")

print("Fetching message list...")
status, messages = imap.search(None, 'ALL')
msg_nums = messages[0].split()
total = len(msg_nums)
print(f"Found {total} emails. Starting download...")

records = []
for idx, num in enumerate(msg_nums, start=1):
    status, msg_data = imap.fetch(num, '(RFC822)')
    raw = msg_data[0][1]
    msg = email.message_from_bytes(raw)

    # Decode headers
    raw_from    = msg.get('From', '')
    sender      = str(make_header(decode_header(raw_from)))
    raw_to      = msg.get('To', '')
    receivers   = str(make_header(decode_header(raw_to)))
    raw_subject = msg.get('Subject', '')
    subject     = str(make_header(decode_header(raw_subject)))

    # Extract plain-text body
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain' and not part.get('Content-Disposition'):
                chunk = part.get_payload(decode=True)
                if chunk:
                    body += chunk.decode(errors='ignore')
    else:
        if msg.get_content_type() == 'text/plain':
            chunk = msg.get_payload(decode=True)
            if chunk:
                body = chunk.decode(errors='ignore')

    message_text = subject + "\n\n" + body
    records.append({
        'sender':    sender,
        'receivers': receivers,
        'message':   message_text
    })

    # Progress log every 50 emails
    if idx % 50 == 0 or idx == total:
        print(f"Processed {idx}/{total} emails")

imap.logout()
print("Logged out from IMAP server.")

# --- WRITE TO CSV ---
csv_file = '../data/raw/gmail_emails.csv'
print(f"Writing {len(records)} records to {csv_file}...")
with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.DictWriter(f, fieldnames=['sender','receivers','message'])
    writer.writeheader()
    for rec in records:
        writer.writerow(rec)

print("Done.")
