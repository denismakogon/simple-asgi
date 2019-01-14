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
from urllib import parse

import multidict

from .request import Request


async def _cancel_tasks(tasks) -> None:
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    for task in tasks:
        if not task.cancelled() and task.exception() is not None:
            raise task.exception()


class ASGIHTTPConnection(object):

    def __init__(self, asgi_app, scope: dict) -> None:
        self.app = asgi_app
        self.scope = scope

    async def __call__(self, receive, send) -> None:
        self.app.access_logger.info(
            "starting a new request <-> response workflow")
        request = self._create_request_from_scope()
        self.app.access_logger.info(
            "request provisioned")
        receiver_task = asyncio.ensure_future(
            self.handle_messages(request, receive))
        handler_task = asyncio.ensure_future(
            self.handle_request(request, send))
        _, pending = await asyncio.wait(
            [handler_task, receiver_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        await _cancel_tasks(pending)

    async def handle_messages(self, request, receive) -> None:
        self.app.access_logger.info(
            "receiving a message")
        while True:
            message = await receive()
            if message['type'] == 'http.request':
                request.body.append(message['body'])
                if not message.get('more_body', False):
                    request.body.set_complete()
            elif message['type'] == 'http.disconnect':
                return

    def _create_request_from_scope(self) -> Request:
        headers = multidict.CIMultiDict()
        headers['Remote-Addr'] = (self.scope.get('client') or ['<local>'])[0]
        for name, value in self.scope['headers']:
            headers.add(name.decode().title(), value.decode())
        if self.scope['http_version'] < '1.1':
            headers.setdefault('Host', self.app.config['SERVER_NAME'] or '')

        path = self.scope["path"]
        path = path if path[0] == "/" else parse.urlparse(path).path

        return self.app.request_class(
            self.scope['method'], self.scope['scheme'], path,
            self.scope['query_string'], headers,
            max_content_length=100 * 1024 * 1024,
            body_timeout=75,
        )

    async def handle_request(self, request: Request, send) -> None:
        self.app.access_logger.info("calling ASGI app request handler")
        try:
            status_code, headers, data = await self.app.handle_request(request)
            self.app.access_logger.info("ASGI app request handler finished")
            await asyncio.wait_for(
                self._send_response(send, status_code, headers, data=data),
                timeout=60)
        except asyncio.TimeoutError:
            pass

    async def _send_response(self, send, status_code, headers, data=None):
        self.app.access_logger.info("sending response back to a caller")
        encoded_headers = [
            (key.lower().encode(), str(value).encode())
            for key, value in headers.items()
        ]
        await send({
            'type': 'http.response.start',
            'status': status_code,
            'headers': encoded_headers,
        })

        if data:
            await send({
                'type': 'http.response.body',
                'body': data,
                'more_body': True,
            })
        await send({
            'type': 'http.response.body',
            'body': b'',
            'more_body': False,
        })
