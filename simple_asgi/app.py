# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import asyncio
import logging
import sys

from hypercorn import config

from . import connection
from . import exceptions
from . import request
from . import runner


class SimpleASGI(object):

    def __init__(
            self,
            name=__name__,
            router=None,
            access_logger=None,
    ):
        self.router = router
        self.name = name
        self.request_class = request.Request
        if access_logger is None:
            self.setup_logger()

    def __call__(self, scope: dict):
        return connection.ASGIHTTPConnection(self, scope)

    def setup_logger(self):
        root = logging.getLogger(__name__)
        root.setLevel(logging.DEBUG)
        ch = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter(
            '%(asctime)s - '
            '%(name)s - '
            '%(levelname)s - '
            '%(message)s'
        )
        ch.setFormatter(formatter)
        root.addHandler(ch)
        self.access_logger = root

    async def handle_request(self, request):
        status_code = 200
        headers = {}
        body = b''
        try:
            handler = self.router.get(request)
            resp = await handler(request)
            status_code = resp.status_code
            headers = resp.headers
            body = resp.get_body()
        except Exception as ex:
            if isinstance(ex, exceptions.BaseASGIException):
                status_code = ex.status_code
                headers = ex.headers
            else:
                status_code = 502
            body = str(ex).encode("utf-8")
        finally:
            return status_code, headers, body

    def run(
            self,
            sock=None,
            debug=None,
            keep_alive_timeout: int=75,
            loop=None,
            asyncio_server_kwargs=None,
    ):

        if loop is None:
            loop = asyncio.get_event_loop()

        cfg = config.Config()
        if debug is not None:
            cfg.debug = debug
            loop.set_debug(debug)
        cfg.error_logger = cfg.access_logger
        cfg.keep_alive_timeout = keep_alive_timeout
        cfg.access_logger = self.access_logger

        runner.run_server(
            self, cfg, loop=loop, sock=sock,
            asyncio_server_kwargs=asyncio_server_kwargs,
        )

    def create_server(
            self,
            sock=None,
            debug=None,
            keep_alive_timeout: int=75,
            loop=None,
            asyncio_server_kwargs=None,
    ):
        if loop is None:
            loop = asyncio.get_event_loop()

        cfg = config.Config()
        if debug is not None:
            cfg.debug = debug
            loop.set_debug(debug)
        cfg.error_logger = cfg.access_logger
        cfg.keep_alive_timeout = keep_alive_timeout
        cfg.access_logger = self.access_logger

        return (
            runner.create_server(
                self, cfg, loop,
                sock=sock,
                asyncio_server_kwargs=asyncio_server_kwargs),
            runner.graceful_shutdown)
