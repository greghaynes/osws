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
import copy

import websockets


class Server(object):
    def __init__(self, host='127.0.0.1', port='9999'):
        self._host = host
        self._port = port
        self._running = False
        self._connected = set()

    @property
    def connections(self):
        return copy.copy(self._connected)

    async def start(self):
        if self._running:
            raise ValueError('Already running')

        self._running = True
        self.server = await websockets.serve(self._handle_ws,
                                             self._host,
                                             self._port)

    async def stop(self):
        self._running = False
        self.server.close()
        await self.server.wait_closed()

    async def _handle_ws(self, websocket, path):
        self._connected.add(websocket)
        while self._running:
            client_read = asyncio.ensure_future(websocket.recv())
            done, pending = await asyncio.wait(
	        [client_read],
                return_when=asyncio.FIRST_COMPLETED
            )

            if client_read in done:
                try:
                    message = client_read.result()
                except websockets.exceptions.ConnectionClosed:
                    pass

        await websocket.close()
        self._connected.remove(websocket)


def main():
    Server().run_forever()


if __name__ == '__main__':
    main()
