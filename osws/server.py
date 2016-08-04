# -*- coding: utf-8 -*-

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import asyncio

import websockets


class Server(object):
    def __init__(self, host='127.0.0.1', port='9999'):
        self._host = host
        self._port = port
        self._running = False

    def run_forever(self):
        self.start()
        asyncio.get_event_loop().run_forever()

    def start(self):
        self._running = True
        ws_server = websockets.serve(self._handle_ws,
                                     self._host,
                                     self._port)
        asyncio.get_event_loop().run_until_complete(ws_server)

    def stop(self):
        self._running = False

    async def _handle_ws(websocket, path):
        while self._running:
            client_read = asyncio.ensure_future(websocket.recv())
            done, pending = await asyncio.wait(
	        [client_read],
                return_when=asyncio.FIRST_COMPLETED
            )

            if client_read in done:
                message = client_read.result()

        websocket.close()


def main():
    Server().run_forever()


if __name__ == '__main__':
    main()
