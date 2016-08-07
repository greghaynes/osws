# -*- coding: utf-8 -*-

# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
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

import fixtures

import asyncio
import testtools


def aio_loop_while(async_fn):
    def async_runner(self):
        async def loop_stop_wrapper(self, loop, async_fn):
            try:
                return await async_fn(self)
            finally:
                loop.stop()

        def exc_handler(loop, ctxt):
            loop.stop()

        loop = asyncio.get_event_loop()
        loop.set_exception_handler(exc_handler)
        loop.run_until_complete(loop_stop_wrapper(self, loop, async_fn))
        loop.run_forever()

    return async_runner


class AsyncFixture(fixtures.Fixture):
    def __init__(self):
        self._async_cleanups = []

    def setUp(self):
        super(AsyncFixture, self).setUp()
        self.addCleanup(self._run_async_cleanups)
        if not asyncio.get_event_loop().is_running():
            self._run_async_setup()

    async def asyncSetUp():
        pass

    def addAsyncCleanUp(self, fn):
        self._async_cleanups.append(fn)

    @aio_loop_while
    async def _run_async_cleanups(self):
        for cleanup in self._async_cleanups:
            await cleanup()

    @aio_loop_while
    async def _run_async_setup(self):
        await self.asyncSetUp()


asynctest = aio_loop_while


class AsyncTestCase(testtools.TestCase):
    async def useAsyncFixture(self, fixture):
        self.useFixture(fixture)
        await fixture.asyncSetUp()
        return fixture


class TestCase(AsyncTestCase):
    """Test case base class for all unit tests."""
