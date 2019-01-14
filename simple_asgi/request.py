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

from simple_asgi import body
from simple_asgi import exceptions


class Request(object):
    """This class represents a request.

    It can be subclassed and the subclassed used in preference by
    replacing the :attr:`~quart.Quart.request_class` with your
    subclass.
    """
    body_class = body.Body

    def __init__(
            self,
            method: str,
            scheme: str,
            path: str,
            query_string: bytes,
            headers,
            *,
            max_content_length=100 * 1024 * 1024,
            body_timeout=75,
    ):
        """Create a request object.

        Arguments:
            method: The HTTP verb.
            scheme: The scheme used for the request.
            path: The full unquoted path of the request.
            query_string: The raw bytes for the query string part.
            headers: The request headers.
            body: An awaitable future for the body data i.e.
                ``data = await body``
            max_content_length: The maximum length in bytes of the
                body (None implies no limit in Quart).
            body_timeout: The maximum time (seconds) to wait for the
                body before timing out.
        """
        self.method = method
        self.schema = scheme
        self.path = path
        self.query_string = query_string
        self.headers = headers
        self.max_content_length = max_content_length
        self.body_timeout = body_timeout
        if (
                self.content_length is not None and
                self.max_content_length is not None and
                self.content_length > self.max_content_length
        ):
            raise body.RequestEntityTooLarge()
        self.body = self.body_class(self.max_content_length)

    async def get_data(self, raw: bool=True):
        """The request body data."""
        body_future = asyncio.ensure_future(self.body)
        try:
            raw_data = await asyncio.wait_for(
                body_future, timeout=self.body_timeout)
        except asyncio.TimeoutError:
            body_future.cancel()
            raise exceptions.RequestTimeout()

        if raw:
            return raw_data
        else:
            return raw_data.decode("utf-8")

    @property
    async def data(self) -> bytes:
        return await self.get_data()

    @property
    def content_encoding(self):
        return self.headers.get('Content-Encoding')

    @property
    def content_length(self):
        if 'Content-Length' in self.headers:
            return int(self.headers['Content-Length'])
        else:
            return None

    @property
    def content_md5(self):
        return self.headers.get('Content-md5')

    @property
    def content_type(self):
        return self.headers.get('Content-Type')
