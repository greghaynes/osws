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
import collections
import copy

import websockets

from osws import exc
from osws import messages


class Connection(object):
    def __init__(self, websocket, subscriptions):
        self.websocket = websocket
        self._subscriptions = subscriptions

    async def handle(self):
        while True:
            client_read = asyncio.ensure_future(self.websocket.recv())
            done, pending = await asyncio.wait(
	        [client_read],
                return_when=asyncio.FIRST_COMPLETED
            )

            if client_read in done:
                try:
                    await self._handle_message(client_read.result())
                except websockets.exceptions.ConnectionClosed:
                    await self.websocket.close()
                    return

    async def _handle_message(self, message):
        try:
            cmd = messages.Command.from_json(message)
            msg = cmd.get_message()
        except exc.InvalidCommandTypeError:
            await self._send_error('Invalid command type')
        except exc.MessageDecodeError:
            await self._send_error('Message decode error')
        else:
            try:
                handler = getattr(self,
                                  '_handle_%s_message' % cmd.get('cmd_type'))
            except AttributeError:
                await self._send_error('Unable to handle command type')
            else:
                await handler(msg)

    async def _handle_ping_message(self, message):
        await self._send_message(
            messages.Pong(payload=message.get('payload'))
        )

    async def _handle_subscribe_message(self, message):
        for service in message.get('services'):
            self._subscriptions.add_subscription(service, self)
        my_services = list(self._subscriptions.get_services(self))
        await self._send_message(messages.Subscriptions(services=my_services))

    async def _send_error(self, error_str):
        await self._send_message(messages.Error(description=error_str))

    async def _send_message(self, msg):
        await self.websocket.send(messages.Command.for_message(msg).to_json())


class SubscriptionMap(object):
    def __init__(self):
        self._service_map = collections.defaultdict(set)
        self._connection_map = collections.defaultdict(set)

    def add_subscription(self, service, connection):
        self._service_map[service].add(connection)
        self._connection_map[connection].add(service)

    def remove_connection(self, connection):
        for service in self._connection_map[connection]:
            self._service_map[service].remove(connection)

    def get_connections(self, service):
        return self._service_map[service]

    def get_services(self, connection):
        return self._connection_map[connection]


class Server(object):
    def __init__(self, notify_source, host='localhost', port='9999'):
        self._host = host
        self._port = port
        self._running = False
        self._connected = set()
        self._subscriptions = SubscriptionMap()
        notify_source.add_message_handler(self._handle_amqp_message)

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

    def stop(self):
        self._running = False
        self.server.close()

    async def wait_closed(self):
        await self.server.wait_closed()

    async def _handle_ws(self, websocket, path):
        conn = Connection(websocket, self._subscriptions)
        self._connected.add(conn)
        try:
            while self._running:
                await conn.handle()
        finally:
            self._subscriptions.remove_connection(conn)
            self._connected.remove(conn)

    def _handle_amqp_message(self, properties, body):
        import pdb;pdb.set_trace()
        print(body)
