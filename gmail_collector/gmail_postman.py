from dataclasses import dataclass, field
import os
import pickle
import json
from pathlib import Path
# Gmail API utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
# for encoding/decoding messages in base64
from base64 import urlsafe_b64decode, urlsafe_b64encode
# for dealing with attachement MIME types
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from mimetypes import guess_type as guess_mime_type 

@dataclass
class GmailPostman_Attr:
    
    email: str = 'a.anurag1024@gmail.com'
    secret_file_path: str = './secrets/gmail_API_client_secret.json'
    mail_dump_folder: str = str(Path('./mount/emails'))
    metadata_dump_folder: str = str(Path('./mount/metadata'))
    download_attachments: bool = False
    
    
class GmailPostman:
    def __init__(self, attr: GmailPostman_Attr):
        self.attr = attr
        self.SCOPES = ['https://mail.google.com/']
        
        self.service = self._gmail_authenticate()
       
        
    def _gmail_authenticate(self):
        creds = None
        # the file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time
        pickle_file = self.attr.secret_file_path.replace('.json', '.pickle')
        if os.path.exists(pickle_file):
            with open(pickle_file, "rb") as token:
                creds = pickle.load(token)
        # if there are no (valid) credentials availablle, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.attr.secret_file_path, self.SCOPES)
                creds = flow.run_local_server(port=0)
            # save the credentials for the next run
            with open(pickle_file, "wb") as token:
                pickle.dump(creds, token)
        return build('gmail', 'v1', credentials=creds)
    
    
    def search_messages(self, query: str):
        """
        
        Search the inbox for messages matching the query
        Please see the search query guidelines: https://support.google.com/mail/answer/7190
        
        """
        result = self.service.users().messages().list(userId='me',q=query).execute()
        messages = [ ]
        if 'messages' in result:
            messages.extend(result['messages'])
        while 'nextPageToken' in result:
            page_token = result['nextPageToken']
            result = self.service.users().messages().list(userId='me',q=query, pageToken=page_token).execute()
            if 'messages' in result:
                messages.extend(result['messages'])
        return messages
    
    
    # Utility Functions
    def get_size_format(b, factor=1024, suffix="B"):
        """
        Scale bytes to its proper byte format
        e.g:
            1253656 => '1.20MB'
            1253656678 => '1.17GB'
        """
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if b < factor:
                return f"{b:.2f}{unit}{suffix}"
            b /= factor
        return f"{b:.2f}Y{suffix}"


    def clean(text):
        # clean text for creating a folder
        return "".join(c if c.isalnum() else "_" for c in text)
    
    
    def parse_parts(self, parts, folder_name, message):
        """
        Utility function that parses the content of an email partition
        """
        contents = {
            'texts': [],
            'htmls': [],
            'attachments': []
        }
        if parts:
            for part in parts:
                filename = part.get("filename")
                mimeType = part.get("mimeType")
                body = part.get("body")
                data = body.get("data")
                file_size = body.get("size")
                part_headers = part.get("headers")
                if part.get("parts"):
                    # recursively call this function when we see that a part
                    # has parts inside
                    contents_ret = self.parse_parts(part.get("parts"), folder_name, message)
                    contents['texts'] += contents_ret['texts']
                    contents['htmls'] += contents_ret['htmls']
                    contents['attachments'] += contents_ret['attachments']
                if mimeType == "text/plain":
                    # if the email part is text plain
                    if data:
                        text = urlsafe_b64decode(data).decode()
                        #print(text)
                    else:
                        text = ""
                    contents['texts'].append(text)
                elif mimeType == "text/html":
                    # if the email part is an HTML content
                    # save the HTML file and optionally open it in the browser
                    if not filename:
                        filename = "index.html"
                    filepath = os.path.join(folder_name, filename)
                    #print("Saving HTML to", filepath)
                    with open(filepath, "wb") as f:
                        f.write(urlsafe_b64decode(data))
                    html_filepath = filepath
                    contents['htmls'].append(html_filepath)
                else:
                    attachment_filepaths = []
                    # attachment other than a plain text or HTML
                    for part_header in part_headers:
                        part_header_name = part_header.get("name")
                        part_header_value = part_header.get("value")
                        if part_header_name == "Content-Disposition":
                            if "attachment" in part_header_value and self.attr.download_attachments:
                                # we get the attachment ID 
                                # and make another request to get the attachment itself
                                #print("Saving the file:", filename, "size:", self.get_size_format(file_size))
                                attachment_id = body.get("attachmentId")
                                attachment = self.service.users().messages() \
                                            .attachments().get(id=attachment_id, userId='me', messageId=message['id']).execute()
                                data = attachment.get("data")
                                filepath = os.path.join(folder_name, filename)
                                if data:
                                    with open(filepath, "wb") as f:
                                        f.write(urlsafe_b64decode(data))
                                    attachment_filepaths.append(filepath)
                                    
                    contents['attachments'] += attachment_filepaths
        return contents
    
    
    def read_message(self, message):
        """
        This function takes Gmail API `service` and the given `message_id` and does the following:
            - Downloads the content of the email
            - Prints email basic information (To, From, Subject & Date) and plain/text parts
            - Creates a folder for each email based on the subject
            - Downloads text/html content (if available) and saves it under the folder created as index.html
            - Downloads any file that is attached to the email and saves it in the folder created
        """
        metadata = {'message_id': message['id']}
        msg = self.service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        # get labels of the message
        metadata['label_ids'] = msg['labelIds']
        # parts can be the message body, or attachments
        payload = msg['payload']
        headers = payload.get("headers")
        parts = payload.get("parts")
        has_subject = False
        if headers:
            # this section prints email basic info & creates a folder for the email
            for header in headers:
                name = header.get("name")
                value = header.get("value")
                if name.lower() == 'from':
                    # we print the From address
                    # print("From:", value)
                    metadata['from'] = value
                if name.lower() == "to":
                    # we print the To address
                    # print("To:", value)
                    metadata['to'] = value
                if name.lower() == "subject":
                    # make our boolean True, the email has "subject"
                    has_subject = True
                    # make a directory with the name of the subject
                    # folder_name = os.path.join(self.attr.mail_dump_folder, self.clean(value))
                    folder_name = os.path.join(self.attr.mail_dump_folder, metadata['message_id'])
                    """
                    # we will also handle emails with the same subject name
                    folder_counter = 0
                    while os.path.isdir(folder_name):
                        folder_counter += 1
                        # we have the same folder name, add a number next to it
                        if folder_name[-1].isdigit() and folder_name[-2] == "_":
                            folder_name = f"{folder_name[:-2]}_{folder_counter}"
                        elif folder_name[-2:].isdigit() and folder_name[-3] == "_":
                            folder_name = f"{folder_name[:-3]}_{folder_counter}"
                        else:
                            folder_name = f"{folder_name}_{folder_counter}"
                    """
                    os.mkdir(folder_name)
                    # print("Subject:", value)
                    metadata['subject'] = value
                if name.lower() == "date":
                    # we print the date when the message was sent
                    # print("Date:", value)
                    metadata['date'] = value
        if not has_subject:
            """
            # if the email does not have a subject, then make a folder with "email" name
            # since folders are created based on subjects
            folder_name = "email"
            if not os.path.isdir(folder_name):
                os.mkdir(folder_name)
            """
            metadata['subject'] = ""
        contents = self.parse_parts(parts, folder_name, message)
        metadata['contents'] = contents
        if not parts:
            # if the email does not have any parts in it
            # then the email is plain text, so we print that
            # this is the case with plain text emails
            text = urlsafe_b64decode(payload["body"]["data"]).decode()
            #print(text)
            if contents:
                metadata['contents']['texts'].append(text)
            else:
                metadata['contents'] = {'texts': [text], 'htmls': [], 'attachments': []}
        
        with open(os.path.join(self.attr.mail_dump_folder, metadata['message_id'], 'message.json'), 'w') as f:
            json.dump(msg, f)
        
        os.makedirs(os.path.join(self.attr.metadata_dump_folder, metadata['message_id']), exist_ok=True)
        with open(os.path.join(self.attr.metadata_dump_folder, metadata['message_id'], 'metadata.json'), 'w') as f:
            json.dump(metadata, f)
        
        return metadata