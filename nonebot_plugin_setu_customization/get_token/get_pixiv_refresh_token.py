from base64 import urlsafe_b64encode
from hashlib import sha256
from pprint import pprint
from secrets import token_urlsafe
from sys import exit
from urllib.parse import urlencode
from webbrowser import open as open_url
from requests import post
from time import sleep

USER_AGENT = "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)"
REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
LOGIN_URL = "https://app-api.pixiv.net/web/v1/login"
AUTH_TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"


def s256(data):
    """S256 transformation method."""
    return urlsafe_b64encode(sha256(data).digest()).rstrip(b"=").decode("ascii")


def oauth_pkce(transform):
    """Proof Key for Code Exchange by OAuth Public Clients (RFC7636)."""
    code_verifier = token_urlsafe(32)
    code_challenge = transform(code_verifier.encode("ascii"))
    return code_verifier, code_challenge


def login():
    code_verifier, code_challenge = oauth_pkce(s256)
    login_params = {
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "client": "pixiv-android",
    }

    open_url(f"{LOGIN_URL}?{urlencode(login_params)}")

    try:
        callback_url = input("粘贴callback链接: ").strip()
    except (EOFError, KeyboardInterrupt):
        return

    code = callback_url[callback_url.find("&code=") + 6 :]
    if code.find("&") != -1:
        code = code[: code.find("&")]

    response = post(
        AUTH_TOKEN_URL,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "code_verifier": code_verifier,
            "grant_type": "authorization_code",
            "include_policy": "true",
            "redirect_uri": REDIRECT_URI,
        },
        headers={"User-Agent": USER_AGENT},
        proxies={"https": "http://127.0.0.1:7890"},
    )

    data = response.json()

    try:
        refresh_token = data["refresh_token"]
    except KeyError:
        print("error:")
        pprint(data)
        exit(1)

    print("client_id:", CLIENT_ID)
    print("client_secret:", CLIENT_SECRET)
    print("refresh_token:", refresh_token)


if __name__ == "__main__":
    print(
        "输入账号密码前记得先按F12，登陆后在网络日志搜索callback，找到类似如下链接\nhttps://app-api.pixiv.net/web/v1/users/auth/pixiv/callback?state=hOOkh2nI5P1SBWOenndWSbcKrT6LsLFKKXERbu0ryAT78N4VJO4CzwLv9336KQ3G&code=vKCHcKqkKyoBj3psh6gILlpL19BpKiRZuC_H3fl9tqM\n\n3秒后打开浏览器"
    )
    sleep(3)
    login()
