from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import base64
import mimetypes
from email.message import EmailMessage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def get_credentials():
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.compose']

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def send_gmail_with_attachment(message: str, attachment: str, subject: str ='Scan Complete', to_addrs: str = 'minhalhasham@icloud.com'):
    """Create and send an email with attachment.
       Print the returned draft's message and id.
      Returns: Send object, including draft id and message meta data.
    """
    creds = get_credentials()

    try:
        # create gmail api client
        service = build('gmail', 'v1', credentials=creds)
        mime_message = EmailMessage()

        # headers
        mime_message['To'] = to_addrs
        mime_message['From'] = 'A Literal Microscope' 
        mime_message['Subject'] = subject

        # text
        mime_message.set_content(
            message + '\n\n' +
            'This is an automated message. Please do not reply.'
        )

        # attachment
        attachment_filename = attachment
        # guessing the MIME type
        type_subtype, _ = mimetypes.guess_type(attachment_filename)
        maintype, subtype = type_subtype.split('/')

        with open(attachment_filename, 'rb') as fp:
            attachment_data = fp.read()
        mime_message.add_attachment(attachment_data, maintype, subtype)

        encoded_message = base64.urlsafe_b64encode(mime_message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }
        # pylint: disable=E1101
        send_message = (service.users().messages().send
                        (userId="me", body=create_message).execute())
        print(F'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(F'An error occurred: {error}')
        send_message = None
    return send_message


# def build_file_part(file):
#     """Creates a MIME part for a file.

#     Args:
#       file: The path to the file to be attached.

#     Returns:
#       A MIME part that can be attached to a message.
#     """
#     content_type, encoding = mimetypes.guess_type(file)

#     if content_type is None or encoding is not None:
#         content_type = 'application/octet-stream'
#     main_type, sub_type = content_type.split('/', 1)
#     if main_type == 'text':
#         with open(file, 'rb'):
#             msg = MIMEText('r', _subtype=sub_type)
#     elif main_type == 'image':
#         with open(file, 'rb'):
#             msg = MIMEImage('r', _subtype=sub_type)
#     elif main_type == 'audio':
#         with open(file, 'rb'):
#             msg = MIMEAudio('r', _subtype=sub_type)
#     else:
#         with open(file, 'rb'):
#             msg = MIMEBase(main_type, sub_type)
#             msg.set_payload(file.read())
#     filename = os.path.basename(file)
#     msg.add_header('Content-Disposition', 'attachment', filename=filename)
#     return msg


# if __name__ == '__main__':
#     gmail_send_message_with_attachment()