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
import json
import random
import traceback

import websockets

from osws import server as osws_server
from osws import messages
from osws.tests import base


def asynctest(async_fn):
    def async_runner(self):
        async def loop_stop_wrapper(self, loop):
            try:
                return await async_fn(self)
            finally:
                loop.stop()

        def exc_handler(loop, ctxt):
            loop.stop()

        loop = asyncio.get_event_loop()
        loop.set_exception_handler(exc_handler)
        loop.run_until_complete(loop_stop_wrapper(self, loop))
        loop.run_forever()

    return async_runner


class TestServer(base.TestCase):
    async def _start_server(self):
        port = random.randint(20000, 60000)
        host = 'localhost'
        server = osws_server.Server(host, port)
        await server.start()
        return server, host, port

    @asynctest
    async def test_connections(self):
        server, host, port = await self._start_server()
        self.assertEqual(0, len(server.connections))
        ws = await websockets.connect('ws://%s:%d/' % (host, port))
        self.assertEqual(1, len(server.connections))
        await ws.close()
        await server.stop()
        self.assertEqual(0, len(server.connections))

    @asynctest
    async def test_command_invalid_type(self):
        server, host, port = await self._start_server()
        ws = await websockets.connect('ws://%s:%d/' % (host, port))
        await ws.send(messages.Command(cmd_type='derp', payload='').to_json())
        resp = await ws.recv()
        self.assertEqual({"payload": {"description": "Invalid command type"},
                          "cmd_type": "error"},
                         json.loads(resp))
        await ws.close()
        await server.stop()

    @asynctest
    async def test_command_unable_to_handle(self):
        server, host, port = await self._start_server()
        ws = await websockets.connect('ws://%s:%d/' % (host, port))
        await ws.send(messages.Command(cmd_type='pong',
                                       payload='{}').to_json())
        resp = await ws.recv()
        self.assertEqual({
            "payload": {"description": "Unable to handle command type"},
            "cmd_type": "error"}, json.loads(resp))
        await ws.close()
        await server.stop()

    @asynctest
    async def test_command_decode_error(self):
        server, host, port = await self._start_server()
        ws = await websockets.connect('ws://%s:%d/' % (host, port))
        await ws.send(messages.Command(cmd_type='ping',
                                       payload='{,}').to_json())
        resp = await ws.recv()
        self.assertEqual({"payload": {"description": "Message decode error"},
                          "cmd_type": "error"},
                         json.loads(resp))
        await ws.close()
        await server.stop()

    @asynctest
    async def test_command_ping(self):
        server, host, port = await self._start_server()
        ws = await websockets.connect('ws://%s:%d/' % (host, port))
        cmd = messages.Command(cmd_type='ping',
                               payload='{"payload": "derp"}')
        await ws.send(cmd.to_json())
        resp = await ws.recv()
        self.assertEqual({'payload': {'payload': 'derp'}, 'cmd_type': 'pong'},
                         json.loads(resp))
        await ws.close()
        await server.stop()
