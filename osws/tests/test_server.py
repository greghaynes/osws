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

import fixtures
import websockets

from osws import messages
from osws import server as osws_server
from osws.tests import base


class FakeConsumer(object):
    def add_message_handler(self, handler):
        pass


class ServerFixture(base.AsyncFixture):
    async def asyncSetUp(self):
        self.port = random.randint(20000, 60000)
        self.host = 'localhost'
        self.server = osws_server.Server(notify_source=FakeConsumer(),
                                         host=self.host, port=self.port)
        self.addAsyncCleanUp(self._clean_up)
        await self.server.start()

    async def _clean_up(self):
        self.server.stop()
        await self.server.wait_closed()


class WebsocketFixture(base.AsyncFixture):
    def __init__(self, host, port):
        super(WebsocketFixture, self).__init__()
        self.host = host
        self.port = port

    async def asyncSetUp(self):
        dest_str = u'ws://%s:%d/' % (self.host, self.port)
        self.addAsyncCleanUp(self._clean_up)
        self.socket = await websockets.connect(dest_str)

    async def _clean_up(self):
        await self.socket.close()


class TestServer(base.AsyncTestCase):
    def setUp(self):
        super(TestServer, self).setUp()
        server_fxtr = self.useFixture(ServerFixture())
        self.server, self.host, self.port = (
            server_fxtr.server, server_fxtr.host, server_fxtr.port
        )

    async def _get_server_ws(self):
        fxtr = await self.useAsyncFixture(
            WebsocketFixture(self.host, self.port)
        )
        return fxtr.socket

    @base.asynctest
    async def test_connections(self):
        self.assertEqual(0, len(self.server.connections))
        socket = await self._get_server_ws()
        self.assertEqual(1, len(self.server.connections))

    @base.asynctest
    async def test_command_invalid_type(self):
        ws = await self._get_server_ws()
        await ws.send(messages.Command(cmd_type='derp', payload='').to_json())
        resp = await ws.recv()
        self.assertEqual({"payload": {"description": "Invalid command type"},
                          "cmd_type": "error"},
                         json.loads(resp))

    @base.asynctest
    async def test_command_unable_to_handle(self):
        ws = await self._get_server_ws()
        await ws.send(messages.Command(cmd_type='pong',
                                       payload='{}').to_json())
        resp = await ws.recv()
        self.assertEqual({
            "payload": {"description": "Unable to handle command type"},
            "cmd_type": "error"}, json.loads(resp))

    @base.asynctest
    async def test_command_decode_error(self):
        ws = await self._get_server_ws()
        await ws.send(messages.Command(cmd_type='ping',
                                       payload='{,}').to_json())
        resp = await ws.recv()
        self.assertEqual({"payload": {"description": "Message decode error"},
                          "cmd_type": "error"},
                         json.loads(resp))

    @base.asynctest
    async def test_command_ping(self):
        ws = await self._get_server_ws()
        cmd = messages.Command(cmd_type='ping',
                               payload='{"payload": "derp"}')
        await ws.send(cmd.to_json())
        resp = await ws.recv()
        self.assertEqual({'payload': {'payload': 'derp'}, 'cmd_type': 'pong'},
                         json.loads(resp))

    @base.asynctest
    async def test_command_subscribe_single(self):
        ws = await self._get_server_ws()
        cmd = messages.Command(cmd_type='subscribe',
                               payload='{"services": ["derp"]}')
        await ws.send(cmd.to_json())
        resp = await ws.recv()
        self.assertEqual(
            {'cmd_type': 'subscriptions', 'payload': {'services': ['derp']}},
            json.loads(resp)
        )

    @base.asynctest
    async def test_command_subscribe_two(self):
        ws = await self._get_server_ws()
        cmd = messages.Command(cmd_type='subscribe',
                               payload='{"services": ["derp1", "derp2"]}')
        await ws.send(cmd.to_json())
        resp = await ws.recv()
        resp_cmp = json.loads(resp)
        resp_cmp['payload']['services'] = set(resp_cmp['payload']['services'])
        self.assertEqual(
            {'cmd_type': 'subscriptions',
             'payload': {'services': set(['derp1', 'derp2'])}},
            resp_cmp
        )
