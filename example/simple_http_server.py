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

import os
import socket


from simple_asgi import app
from simple_asgi import response
from simple_asgi import router


async def hello(request):
    request_body = await request.data
    return response.Response(body=request_body)

sock_path = "/tmp/fn.sock"
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

try:
    os.remove(sock_path)
finally:
    sock.bind("/tmp/fn.sock")

rtr = router.Router()
rtr.add("/call", ["POST"], hello)
http_app = app.SimpleASGI(name=__name__, router=rtr)

http_app.run(sock=sock)
