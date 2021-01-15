import unittest
import asyncio
from wander import Wandbox


class TestWanderMethods(unittest.TestCase):

	def test_connect(self):

		async def coro():
			inst = Wandbox()
			self.assertTrue(inst.session is not None)

		asyncio.run(coro())

	def test_list(self):

		async def coro():
			inst = Wandbox()
			x = await inst.compilers()
			self.assertTrue(isinstance(x, list))

		asyncio.run(coro())

	def test_permlink(self):

		async def coro():
			inst = Wandbox()
			x = await inst.get_permlink(link="axZAlgGHXxxMY18o")
			self.assertTrue(isinstance(x, dict))

		asyncio.run(coro())

	def test_template(self):

		async def coro():
			inst = Wandbox()
			x = await inst.get_template(name="gcc")
			self.assertTrue(isinstance(x, str), msg=x)

		asyncio.run(coro())

	def test_compile_simple(self):

		async def coro():
			inst = Wandbox()

			code = "import os\nprint(os.name)\nprint('done')"
			x = await inst.compile(
				code=code,
				compiler='cpython-3.8.0',
				compiler_option_raw=False,
				runtime_option_raw=True
			)
			keys = ('program_message', 'program_output', 'status')
			self.assertTrue(sorted(x.keys()) == sorted(keys), msg=f"{x}\n-----\n{keys}")

		asyncio.run(coro())

	def test_compile_save(self):

		async def coro():
			inst = Wandbox()

			code = "import os\nprint(os.name)\nprint('done')"
			x = await inst.compile(
				code=code,
				compiler='cpython-3.8.0',
				compiler_option_raw=False,
				runtime_option_raw=True,
				save=True
			)
			keys = ('program_message', 'program_output', 'status', 'permlink', 'url')
			self.assertTrue(sorted(x.keys()) == sorted(keys), msg=f"{x}\n-----\n{keys}")

		asyncio.run(coro())

	def test_compile_codes(self):

		async def coro():
			inst = Wandbox()

			codes = [{'file': 'demo.py', 'code': "import os\nname=os.name\nsecret=os.cpu_count()"}]
			code = "import demo\nprint(demo.name, demo.secret)\nprint('done')"
			x = await inst.compile(
				code=code,
				codes=codes,
				compiler='cpython-3.8.0',
				compiler_option_raw=False,
				runtime_option_raw=True
			)
			keys = ('program_message', 'program_output', 'status')
			self.assertTrue(sorted(x.keys()) == sorted(keys), msg=f"{x}\n-----\n{keys}")

		asyncio.run(coro())

	def test_compile_nd_simple(self):

		async def coro():
			inst = Wandbox()

			code = "import os\nprint(os.name)\nprint('done')"
			x = await inst.compile_nd(
				code=code,
				compiler='cpython-3.8.0',
				compiler_option_raw=False,
				runtime_option_raw=True
			)
			keys = ['data', 'type']
			self.assertTrue(all(sorted(doc.keys()) == keys for doc in x), msg=f"{keys}\n-----\n{x}")

		asyncio.run(coro())


if __name__ == "__main__":
	unittest.main()
