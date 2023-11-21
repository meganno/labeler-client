import asyncio
import os
import subprocess
import sys
import time
import webbrowser

import pydash
import requests
import websockets
from websockets import exceptions as ws_exceptions

from labeler_client.constants import DNS_NAME, SERVICE_ENDPOINTS
from labeler_client.helpers import get_request


class Authentication:
    def __init__(self, host=None, project="base", access_token=None):
        if not pydash.is_empty(host) and pydash.is_empty(project):
            raise Exception("Project cannot be None or empty.")
        self.id_token = None
        self.host = host
        self.access_token = access_token
        self.project = project
        self.process = None
        self.stop = None
        if pydash.is_empty(host):
            self.project = "base"
        if not pydash.is_empty(project):
            self.project = project
        response = get_request(
            path=self.get_service_endpoint() + "?url_check=1", timeout=5
        )
        if response.status_code != 200:
            raise Exception(response.text)
        self.__WEB_PORT = 52235
        self.__SOCKET_PORT = 52236
        if pydash.is_empty(access_token):
            self.__start_servers()

    def __start_servers(self):
        path = os.path.dirname(__file__)
        try:
            self.process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "http.server",
                    str(self.__WEB_PORT),
                    "-b",
                    "localhost",
                    "-d",
                    f"{path}/web/auth/out",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            time.sleep(2)
            webbrowser.open(f"http://localhost:{self.__WEB_PORT}")
            self.stop = asyncio.Future()

            async def handler(websocket):
                while True:
                    try:
                        id_token = await websocket.recv()
                    except ws_exceptions.ConnectionClosedOK:
                        break
                self.stop.set_result(id_token)

            async def main():
                async with websockets.serve(handler, "", self.__SOCKET_PORT):
                    self.__set_id_token(await self.stop)
                    self.process.terminate()

            asyncio.run(main())
        except OSError as ex:
            if not pydash.is_empty(self.process):
                self.process.terminate()
            raise Exception(ex)
        except KeyboardInterrupt as ex:
            self.stop.set_result(None)

    def reauthenticate(self):
        self.__start_servers()

    def get_id_token(self):
        return str(self.id_token)

    def get_path(self):
        # megagon load balancer
        dns_name = DNS_NAME
        if self.host is not None and len(self.host) > 0:
            dns_name = self.host
        return f"{dns_name}:5000/{self.project}/tokens"

    def get_service_endpoint(self, key=None):
        dns_name = DNS_NAME
        if self.host is not None:
            dns_name = self.host
        return (
            "{}:5000/".format(dns_name) + self.project + SERVICE_ENDPOINTS.get(key, "")
        )

    def get_access_tokens(self, job=False):
        payload = {"id_token": self.id_token, "job": job}
        response = get_request(self.get_path(), json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def create_access_token(
        self, note: str = "", expiration_duration: int = 14, demo=False, job=False
    ):
        payload = {}
        if not pydash.is_empty(self.id_token):
            payload.update({"id_token": self.id_token})
        elif not pydash.is_empty(self.access_token):
            payload.update({"access_token": self.access_token})
        payload.update(
            {
                "note": note,
                "expiration_duration": expiration_duration,
                "demo": demo,
                "job": job,
            }
        )
        response = requests.post(self.get_path(), json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def delete_access_tokens(self, id_list: list = []):
        payload = {"id_token": self.id_token}
        payload.update({"id_list": id_list})
        response = requests.delete(self.get_path(), json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def __set_id_token(self, token):
        if token == "":
            token = None
        self.id_token = token

    def __del__(self):
        if not pydash.is_empty(self.process):
            self.process.terminate()
        if not pydash.is_empty(self.stop):
            self.stop.set_result(None)
