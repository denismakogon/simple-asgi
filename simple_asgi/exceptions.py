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


class BaseASGIException(Exception):
    def __init__(self, reason, status=404, headers=None):
        self.status_code = status
        self.headers = headers if headers else {}
        super(BaseASGIException, self).__init__(reason)


class NotFound(BaseASGIException):
    pass


class InvalidUsage(BaseASGIException):
    pass


class MethodNotSupported(BaseASGIException):
    def __init__(self, message, method, allowed_methods):
        super().__init__(message, status=405)
        self.headers = dict()
        self.headers["Allow"] = ", ".join(allowed_methods)
        if method in ["HEAD", "PATCH", "PUT", "DELETE"]:
            self.headers["Content-Length"] = 0


class RequestEntityTooLarge(BaseASGIException):

    def __init__(self):
        super(RequestEntityTooLarge, self).__init__(
            "request size is too large")


class RequestTimeout(BaseASGIException):

    def __init__(self):
        super(RequestTimeout, self).__init__(
            "request timeout")


class RouteExists(Exception):
    pass


class RouteDoesNotExist(Exception):
    pass


class ParameterNameConflicts(Exception):
    pass
