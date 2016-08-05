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

from osws import messages
from osws.tests import base


class SimpleMessage(messages.Message):
    properties = ['simple_prop1']


class ComplexMessage(messages.Message):
    properties = ['complex_prop1']
    sub_messages = {'sub_msg1': SimpleMessage}


class TestMessage(base.TestCase):
    def test_simple_to_json(self):
        msg = SimpleMessage(simple_prop1='simple_prop1_val')
        self.assertEqual({"simple_prop1": "simple_prop1_val"},
                         json.loads(msg.to_json()))

    def test_simple_from_json(self):
        msg = SimpleMessage.from_json('{"simple_prop1": "simple_prop1_val"}')
        self.assertEqual('simple_prop1_val', msg.get('simple_prop1'))
        self.assertEqual(True, isinstance(msg, SimpleMessage))

    def test_complex_to_json(self):
        msg = ComplexMessage(complex_prop1='complex_prop1_val',
                             sub_msg1={"simple_prop1": "simple_prop1_val"})
        self.assertEqual({'complex_prop1': 'complex_prop1_val',
                          'sub_msg1': {"simple_prop1": "simple_prop1_val"}},
                         json.loads(msg.to_json()))

    def test_complext_from_json(self):
        msg = ComplexMessage.from_json(
            '{"complex_prop1": "complex_prop1_val", "sub_msg1": '
            '{"simple_prop1": "simple_prop1_val"}}')
        self.assertEqual('complex_prop1_val', msg.get('complex_prop1'))
        self.assertEqual(True, isinstance(msg, ComplexMessage))
        self.assertEqual(True, isinstance(msg.get('sub_msg1'), SimpleMessage))
