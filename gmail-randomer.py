from __future__ import print_function

import os.path
import sys
import random

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

console = Console()


def search_messages(service, query):
    result = service.users().messages().list(userId="me", q=query).execute()
    messages = []
    if "messages" in result:
        messages.extend(result["messages"])
    while "nextPageToken" in result:
        page_token = result["nextPageToken"]
        result = (
            service.users()
            .messages()
            .list(userId="me", q=query, pageToken=page_token)
            .execute()
        )
        if "messages" in result:
            messages.extend(result["messages"])
    return messages


def main(args):
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        if len(args) == 1: 
            messages = search_messages(service, "in:inbox")
        else:
            messages = search_messages(service, " ".join(args[1:]))

        msg = random.choice(messages)
        content = (
            service.users()
            .messages()
            .get(userId="me", id=msg["id"], format="full")
            .execute()
        )
        #print(content)

        msg_id = content["id"]
        URL_msg = f"https://mail.google.com/mail/u/0/#inbox/{msg_id}"
        snippet = content["snippet"]
        headers = content["payload"]["headers"]
        subject = None
        for header in headers:
            if header["name"] == "Subject":
                subject = header["value"]
            if header["name"] == "From":
                email_from = header["value"]
        
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="left")
        grid.add_row("[white]-[/] [yellow]From[/]: ", f"[green]{email_from}[/]")
        grid.add_row("[white]-[/] [yellow]Subject[/]: ", f"{subject}")
        grid.add_row("[white]-[/] [yellow]Access[/]: ", f"{URL_msg}")
        console.print(Panel.fit(grid, title="[yellow]Random Message ![/]"))

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


if __name__ == "__main__":

    main(sys.argv)
