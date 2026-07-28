from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin

import requests
import urllib3
from bs4 import BeautifulSoup

from .models import DeviceStatus
from .parser import parse_status_html
from .security import create_login_values

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RouterError(RuntimeError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class LoginResult:
    final_url: str
    status_code: int


class RouterClient:
    def __init__(
        self,
        host: str,
        protocol: str = "https",
        timeout: float = 10.0,
        verify_tls: bool = False,
        debug: Callable[[str], None] | None = None,
    ):
        host = host.strip().rstrip("/")
        if "://" in host:
            self.base_url = host + "/"
        else:
            self.base_url = f"{protocol}://{host}/"

        self.timeout = timeout
        self.verify_tls = verify_tls
        self.debug = debug or (lambda _: None)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Router-OQC-Status-Tool/0.1.0",
            "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        })

    def close(self) -> None:
        self.session.close()

    def _get(self, path: str, **kwargs) -> requests.Response:
        url = urljoin(self.base_url, path)
        self.debug(f"GET {url}")
        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                verify=self.verify_tls,
                **kwargs,
            )
            self.debug(f"GET status={response.status_code} bytes={len(response.content)}")
            return response
        except requests.Timeout as exc:
            raise RouterError("CONNECT_TIMEOUT", "連線逾時") from exc
        except requests.ConnectionError as exc:
            raise RouterError("CONNECTION_FAILED", "無法連線至Router") from exc
        except requests.RequestException as exc:
            raise RouterError("HTTP_ERROR", str(exc)) from exc

    def _post(self, path: str, data: dict[str, str], **kwargs) -> requests.Response:
        url = urljoin(self.base_url, path)
        self.debug(f"POST {url}; fields={list(data.keys())}")
        try:
            response = self.session.post(
                url,
                data=data,
                timeout=self.timeout,
                verify=self.verify_tls,
                **kwargs,
            )
            self.debug(
                f"POST status={response.status_code} final_url={response.url} "
                f"bytes={len(response.content)}"
            )
            return response
        except requests.Timeout as exc:
            raise RouterError("CONNECT_TIMEOUT", "登入連線逾時") from exc
        except requests.ConnectionError as exc:
            raise RouterError("CONNECTION_FAILED", "登入時無法連線至Router") from exc
        except requests.RequestException as exc:
            raise RouterError("HTTP_ERROR", str(exc)) from exc

    def get_login_page(self) -> tuple[str, str]:
        response = self._get("admin/login.asp", allow_redirects=True)
        if response.status_code != 200:
            raise RouterError("LOGIN_PAGE_HTTP_ERROR", f"登入頁HTTP {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        token = soup.find("input", attrs={"name": "csrftoken"})
        if not token or not token.get("value"):
            raise RouterError("LOGIN_CSRF_NOT_FOUND", "找不到登入頁csrftoken")

        return response.text, str(token["value"])

    def login(self, username: str, password: str) -> LoginResult:
        _, csrf_token = self.get_login_page()
        encoded_password, security_flag = create_login_values(username, password)

        payload = {
            "username": username,
            "encodePassword": encoded_password,
            "save": "Log In",
            "submit-url": "/admin/login.asp",
            "postSecurityFlag": str(security_flag),
            "csrftoken": csrf_token,
        }

        response = self._post(
            "boaform/admin/formLogin",
            data=payload,
            allow_redirects=True,
            headers={"Referer": urljoin(self.base_url, "admin/login.asp")},
        )

        text = response.text.lower()
        if "device login" in text and "name=\"encodepassword\"" in text:
            raise RouterError("AUTHENTICATION_FAILED", "帳號或密碼錯誤")

        # Stronger validation: authenticated status page must be accessible.
        probe = self._get(f"status.asp?v={int(time.time() * 1000)}", allow_redirects=True)
        probe_text = probe.text
        if (
            probe.status_code != 200
            or "Device Status" not in probe_text
            or "Device Name" not in probe_text
        ):
            if "Device Login" in probe_text:
                raise RouterError("AUTHENTICATION_FAILED", "登入後仍被導回登入頁")
            raise RouterError("SESSION_INVALID", "登入後無法存取Device Status")

        return LoginResult(final_url=response.url, status_code=response.status_code)

    def fetch_status(self) -> tuple[DeviceStatus, str]:
        url_path = f"status.asp?v={int(time.time() * 1000)}"
        response = self._get(
            url_path,
            allow_redirects=True,
            headers={"Referer": self.base_url},
        )
        if response.status_code != 200:
            raise RouterError("STATUS_PAGE_HTTP_ERROR", f"Status頁HTTP {response.status_code}")
        if "Device Login" in response.text:
            raise RouterError("SESSION_EXPIRED", "Session已失效")
        try:
            status = parse_status_html(response.text, response.url)
        except ValueError as exc:
            raise RouterError("STATUS_PARSE_ERROR", str(exc)) from exc
        return status, response.text

    def logout(self) -> None:
        try:
            self._get("admin/logout2.asp", allow_redirects=False)
        except Exception:
            pass
