import io
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ===== 設定 =====
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

def get_service():
    creds = None
    token_path = os.path.join(BASE_DIR, "token.json")
    cred_path = os.path.join(BASE_DIR, "credentials.json")

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(cred_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    return build("drive", "v3", credentials=creds)

def main():
    service = get_service()

    query = f"mimeType='application/json'"

    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        print("No files found.")
        return

    for file in files:
        file_id = file["id"]
        name = file["name"]
        path = os.path.join(name)

        print(f"Downloading {name}")

        request = service.files().get_media(fileId=file_id)
        fh = io.FileIO(path, "wb")
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

    print("Download complete.")

if __name__ == "__main__":
    main()
