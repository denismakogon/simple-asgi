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

from collections import namedtuple
from functools import lru_cache

from . import exceptions

ROUTER_CACHE_SIZE = 1024
Route = namedtuple(
    "Route", ["handler", "methods"]
)


class Router(object):

    def __init__(self):
        self.__router_map = {}

    def add(self, path, methods, handler):
        self.__router_map[path] = Route(handler=handler, methods=methods)

    @lru_cache(maxsize=ROUTER_CACHE_SIZE)
    def get(self, request):
        try:
            rt = self.__router_map[request.path]
            if request.method not in rt.methods:
                raise exceptions.MethodNotSupported(
                    "Method {0} for path {1} not allowed"
                    .format(request.method, request.path),
                    request.method, rt.methods)
            return rt.handler
        except Exception as ex:
            if isinstance(ex, KeyError):
                raise exceptions.RouteDoesNotExist(
                    "Route was not registered: {}"
                    .format(request.path))
            else:
                raise ex
