"""Constants for the Livly integration."""

DOMAIN = "livly"

# API endpoints
AUTH_BASE_URL = "https://login.livly.io"
API_BASE_URL = "https://api.livly.io"

ENDPOINT_PASSWORDLESS_START = f"{AUTH_BASE_URL}/passwordless/start"
ENDPOINT_OAUTH_TOKEN = f"{AUTH_BASE_URL}/oauth/token"
ENDPOINT_USER_ME = f"{API_BASE_URL}/api/livly/users/me"
ENDPOINT_PACKAGES_FILTERED = f"{API_BASE_URL}/api/livly/packages/user/{{user_id}}/filtered"

# Auth constants
AUTH_CLIENT_ID = "ubEvB5okpRuQswblDO2MPYyDScnI2hGn"
OAUTH_SCOPE = "openid profile email offline_access"
OAUTH_GRANT_TYPE_OTP = "http://auth0.com/oauth/grant-type/passwordless/otp"
OAUTH_GRANT_TYPE_REFRESH = "refresh_token"  # May need adjustment - untested

# API headers
DEFAULT_HEADERS = {
    "Accept": "application/json",
    "Accept-Encoding": "gzip",
    "Connection": "Keep-Alive",
    "Content-Type": "application/json",
    "Host": "api.livly.io",
    "User-Agent": "okhttp/4.12.0",
    "X-APP-ID": "com.livly.android.livly_resident",
}

# Update interval (30 minutes)
UPDATE_INTERVAL_MINUTES = 30

# Config keys
CONF_PHONE_NUMBER = "phone_number"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ID_TOKEN = "id_token"
CONF_TOKEN_EXPIRES_AT = "token_expires_at"
CONF_USER_ID = "user_id"
