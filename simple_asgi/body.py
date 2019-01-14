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

from .exceptions import RequestEntityTooLarge


class Body(object):
    """A request body container.

    The request body can either be iterated over and consumed in parts
    (without building up memory usage) or awaited.

    .. code-block:: python

        async for data in body:
            ...
        # or simply
        complete = await body

    Note: It is not possible to iterate over the data and then await
    it.
    """

    def __init__(self, max_content_length) -> None:
        self._data = bytearray()
        self._complete: asyncio.Event = asyncio.Event()
        self._has_data: asyncio.Event = asyncio.Event()
        self._max_content_length = max_content_length

    def __aiter__(self) -> 'Body':
        return self

    async def __anext__(self) -> bytes:
        # if we got all of the data in the first shot, then self._complete is
        # set and self._has_data will not get set again, so skip the await
        # if we already have completed everything
        if not self._complete.is_set():
            await self._has_data.wait()

        if self._complete.is_set() and len(self._data) == 0:
            raise StopAsyncIteration()

        data = bytes(self._data)
        self._data.clear()
        self._has_data.clear()
        return data

    def __await__(self):
        yield from self._complete.wait().__await__()
        return bytes(self._data)

    def append(self, data: bytes) -> None:
        if data == b'':
            return
        self._data.extend(data)
        self._has_data.set()
        if (self._max_content_length is not None and
                len(self._data) > self._max_content_length):
            raise RequestEntityTooLarge()

    def set_complete(self) -> None:
        self._complete.set()
        self._has_data.set()

    def set_result(self, data: bytes) -> None:
        """Convienience method, mainly for testing."""
        self.append(data)
        self.set_complete()
