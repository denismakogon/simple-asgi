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


from hypercorn.asyncio import run


def create_server(
        asgi_app, cfg, loop=None,
        sock=None, asyncio_server_kwargs=None
) -> asyncio.AbstractServer:
    """Creates a server to run the app on given the options."""

    if loop is None:
        loop = asyncio.get_event_loop()

    loop.set_debug(cfg.debug)

    ssl_context = cfg.create_ssl_context()

    asyncio_server_kwargs = (asyncio_server_kwargs if
                             asyncio_server_kwargs else {})

    create_server_coro = loop.create_server(
        lambda: run.Server(asgi_app, loop, cfg),
        backlog=cfg.backlog,
        ssl=ssl_context,
        sock=sock,
        **asyncio_server_kwargs,
    )

    server = loop.run_until_complete(create_server_coro)

    return server


def cancel_all_other_tasks(loop: asyncio.AbstractEventLoop):
    tasks = asyncio.all_tasks(loop)
    for task in tasks:
        task.cancel()
    loop.run_until_complete(
        asyncio.gather(
            *tasks, loop=loop, return_exceptions=True
        )
    )

    for task in tasks:
        if not task.cancelled() and task.exception() is not None:
            loop.call_exception_handler(
                {
                    "message": "unhandled exception during shutdown",
                    "exception": task.exception(),
                    "task": task,
                }
            )


def run_server(
        asgi_app, cfg,
        loop=None, sock=None,
        asyncio_server_kwargs=None):
    """Runs a server to run the app on given the options"""
    server = create_server(
        asgi_app, cfg, loop=loop, sock=sock,
        asyncio_server_kwargs=asyncio_server_kwargs)
    try:
            loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        graceful_shutdown(server, loop)


def graceful_shutdown(server: asyncio.AbstractServer, loop):
    server.close()
    loop.run_until_complete(server.wait_closed())
    cancel_all_other_tasks(loop)
    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.close()
