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

import osws.config
from osws import consumer
from osws import server


def get_config():
    return osws.config.config_opts


def main(argv=None):
    conf = get_config()

    nc = consumer.NotificationConsumer(
        'amqp://stackrabbit:asdf@localhost:5672/%2F',
        'notifications.info'
    )

    srv = server.Server(notify_source=nc,
                        host=conf.bind_host,
                        port=conf.bind_port)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(srv.start())
    try:
        loop.run_forever()
    finally:
        srv.stop()
