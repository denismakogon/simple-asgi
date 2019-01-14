# Simple ASGI HTTP 1.1 server implementation

This framework was inspired by [hypercorn](https://pgjones.gitlab.io/hypercorn/index.html) framework.

## How to install

```bash
pip install simple-asgi
```

## Example

```python
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

```
