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


class Response(object):

    def __init__(self, status_code=200, headers=None, body=None):
        self.status_code = status_code
        self.headers = headers if headers else {}
        self.body = body if body else b''

    def get_body(self):
        if isinstance(self.body, bytes):
            return self.body
        else:
            return str(self.body).encode("utf-8")
