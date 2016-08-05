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

import json

from osws import exc


class Message(object):
    properties = []
    sub_messages = {}

    @classmethod
    def from_json(cls, json_str):
        try:
            flattened = json.loads(json_str)
        except json.decoder.JSONDecodeError:
            raise exc.MessageDecodeError()
        return cls(**flattened)

    def __init__(self, **kwargs):
        self._properties = {}
        self._sub_messages = {}
        for key, val in kwargs.items():
            if key in self.properties:
                self._properties[key] = val
            elif key in self.sub_messages:
                self._sub_messages[key] = self.sub_messages[key](**val)
            else:
                raise exc.InvalidMessagePropertyError(
                    '%s is not a valid property' % key
                )

    def flatten(self):
        res = {}
        for prop in self.properties:
            res[prop] = self._properties[prop]
        for prop, msg_type in self.sub_messages.items():
            res[prop] = self._sub_messages[prop].flatten()
        return res

    def to_json(self):
        return json.dumps(self.flatten())

    def get(self, key):
        try:
            return self._properties[key]
        except KeyError:
            return self._sub_messages[key]


class Error(Message):
    properties = ['description']


class Ping(Message):
    properties = ['payload']


class Pong(Message):
    properties = ['payload']


def bijective_dict(src):
    ret = {}
    for key, val in src.items():
        ret[key] = val
        ret[val] = key
    return ret


class Command(Message):
    types = bijective_dict({
        'error': Error,
        'ping': Ping,
        'pong': Pong
    })

    properties = ['cmd_type', 'payload']

    @classmethod
    def for_message(cls, message):
        return Command(cmd_type=cls.types[type(message)], 
                       payload=message.flatten())

    def get_message(self):
        try:
            msg_type = self.types[self.get('cmd_type')]
        except KeyError:
            raise exc.InvalidCommandTypeError()
        return msg_type.from_json(self.get('payload'))
