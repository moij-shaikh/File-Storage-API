from config import email_pass , sender , SUPABASE_SECRET_KEY , SUPABASE_URL

from pwdlib import PasswordHash

pass_hasher=PasswordHash.recommended()

import smtplib

from email.message import EmailMessage
def send_email_to_verify(email,url):
    msg=EmailMessage()
    msg["From"]=sender
    msg["TO"]=email
    msg["Subject"]="Verify Email"
    msg.set_content(f"""
    <a href={url}>Click to verify</a>
""")
    smtp=smtplib.SMTP_SSL("smtp.gmail.com",465)
    smtp.login(sender,email_pass)
    smtp.send_message(msg)
    return "Sended"


import clamd
scanner=clamd.ClamdUnixSocket("/run/clamav/clamd.ctl")
    

import supabase
supabase=supabase.acreate_client(SUPABASE_URL, SUPABASE_SECRET_KEY)
drive=supabase.storage.from_('drive')