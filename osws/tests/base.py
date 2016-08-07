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


class AsyncFixture(fixtures.Fixture):
    async def asyncSetUp(self):
        pass

    async def asyncCleanUp(self):
        pass

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


asynctest = aio_loop_while


class AsyncTestCase(testtools.TestCase):
    def setUp(self):
        super(AsyncTestCase, self).setUp()
        self._async_cleanups = []
        self.loop = asyncio.get_event_loop()
        self.addCleanup(self._run_async_cleanups)
        self._run_async_setups()

    async def asyncSetUp(self):
        pass

    @aio_loop_while
    async def _run_async_setups(self):
        await self.asyncSetUp()

    def addAsyncCleanup(self, cleanup, *args, **kwargs):
        self._async_cleanups.append((cleanup, args, kwargs))

    async def useAsyncFixture(self, fixture):
        await fixture.asyncSetUp()
        self.addAsyncCleanup(fixture.asyncCleanUp)
        return self.useFixture(fixture)

    @aio_loop_while
    async def _run_async_cleanups(self):
            for cleanup, args, kwargs in self._async_cleanups:
                await cleanup(*args, **kwargs)


class TestCase(AsyncTestCase):
    """Test case base class for all unit tests."""
