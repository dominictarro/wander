import unittest
import asyncio
from wander.client import Wandbox


# TODO, pseudo-API to test methods?
class TestMethod(unittest.TestCase):

	def test_connect(self):
		asyncio.run(Wandbox.connect())
		self.assertTrue(Wandbox.session is not None)

