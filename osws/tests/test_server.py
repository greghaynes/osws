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

from osws import server
from osws.tests import base

import websockets


def asynctest(async_fn):
    def async_runner(self=None):
        loop = asyncio.get_event_loop()
        def on_done(future):
            loop.stop()
        test_future = asyncio.ensure_future(async_fn(self))
        test_future.add_done_callback(on_done)
        loop.run_forever()
    return async_runner


class TestServer(base.TestCase):
    def setUp(self):
        super(TestServer, self).setUp()
        self.server = server.Server()

    @asynctest
    async def test_server_connections(self):
        await self.server.start()
        self.assertEqual(0, len(self.server.connections))
        ws = await websockets.connect('ws://127.0.0.1:9999/')
        self.assertEqual(1, len(self.server.connections))
        await ws.close()
        await self.server.stop()
        self.assertEqual(0, len(self.server.connections))
