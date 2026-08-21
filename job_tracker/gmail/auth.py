from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def authenticate(credentials_file: Path, token_file: Path):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    credentials = Credentials.from_authorized_user_file(str(token_file), SCOPES) if token_file.exists() else None
    if credentials and credentials.expired and credentials.refresh_token: credentials.refresh(Request())
    if not credentials or not credentials.valid:
        if not credentials_file.exists(): raise FileNotFoundError(f"OAuth credentials not found: {credentials_file}")
        credentials = InstalledAppFlow.from_client_secrets_file(str(credentials_file), SCOPES).run_local_server(port=0)
    token_file.write_text(credentials.to_json())
    return credentials

