import msal
from django.conf import settings

def build_msal_app(cache=None):
    return msal.ConfidentialClientApplication(
        settings.MSAL_CLIENT_SECRET,
        authority=f"https://login.microsoftonline.com/{settings.MSAL_TENANT_ID}",
        client_credential=settings.MSAL_CLIENT_SECRET,
        token_cache=cache
    )

def get_sign_in_flow():
    app = build_msal_app()
    return app.initiate_auth_code_flow(
        [ "User.Read" ],
        redirect_uri=settings.MSAL_REDIRECT_URI
    )
