import aiohttp
import asyncio
import atexit
import json
import ndjson
import typing


class Wandbox(object):
    url = "https://wandbox.org/api/{0}"
    active = []

    def __init__(self):
        """
        Instantiate an aiohttp session unique to the instance

        """
        self.session = None
        self.connect()

    def connect(self):
        """
        Creates an aiohttp session for handling Wandbox API communication

        :return:
        """
        if self.session is None:
            self.session: aiohttp.ClientSession = aiohttp.ClientSession()
            Wandbox.active.append(self)
        else:
            if self.session.closed:
                self.session = aiohttp.ClientSession()
            if self not in Wandbox.active:
                Wandbox.active.append(self)

    async def close(self):
        """
        Closes aiohttp session if still open

        :return:
        """
        if self.session is not None and not self.session.closed:
            await self.session.close()
            Wandbox.active.remove(self)

    @staticmethod
    async def _parse_response(response: aiohttp.ClientResponse) -> typing.Any:
        """
        Takes an aiohttp.ClientResponse object and converts content to Python primitives via json or ndjson

        :param response:
        :return:
        """
        decoder = ndjson.Decoder if (response.content_type == 'application/x-ndjson') else json.JSONDecoder
        # TODO: Appears to be a bug in response.get_encoding() when dealing with ndjson
        charset = response.charset # if response.charset is not None else response.get_encoding()
        return await response.json(content_type=response.content_type, loads=decoder().decode, encoding=charset)

    async def _get(self, url, *args, **kwargs):
        """
        Performs GET request on given URL. Modifies aiohttp GET behavior with args and kwargs.

        :param url:
        :param args:
        :param kwargs:
        :return:
        """
        # TODO: drop ssl keyword once bug fixed
        async with self.session.get(*args, url=url, ssl=False, **kwargs) as response:
            response.raise_for_status()
            return await self._parse_response(response)

    async def _post(self, url, *args, **kwargs):
        """
        Performs POST request on given URL. Modifies aiohttp POST behavior with args and kwargs.

        :param url:
        :param args:
        :param kwargs:
        :return:
        """
        # TODO: drop ssl keyword once bug fixed
        async with self.session.post(*args, url=url, ssl=False, **kwargs) as response:
            response.raise_for_status()
            return await self._parse_response(response)

    async def compilers(self, **kwargs) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Requests the compiler list at https://wandbox.org/api/list.json

        :param kwargs:  Keyword arguments to modify aiohttp ClientSession().get() method
        :return:        List of compiler data (dictionaries)

        ```
        compilers = await Wandbox.compilers()
        compilers == [{
              "compiler-option-raw":true,
              "runtime-option-raw":false,
              "display-compile-command":"g++ prog.cc",
              "switches":[{
                "default":true,
                "name":"warning",
                "display-flags":"-Wall -Wextra",
                "display-name":"Warnings"
              },{
                "default":false,
                "name":"optimize",
                "display-flags":"-O2 -march=native",
                "display-name":"Optimization"
              },{
                "default":false,
                "name":"cpp-verbose",
                "display-flags":"-v",
                "display-name":"Verbose"
              },{
                "default":"boost-1.55",
                "options":[{
                  "name":"boost-nothing",
                  "display-flags":"",
                  "display-name":"Don't Use Boost"
                },{
                  "name":"boost-1.47",
                  "display-flags":"-I/usr/local/boost-1.47.0/include",
                  "display-name":"Boost 1.47.0"
                },{
                  "name":"boost-1.48",
                  "display-flags":"-I/usr/local/boost-1.48.0/include",
                  "display-name":"Boost 1.48.0"
                },{
                  ...
                },{
                  "name":"boost-1.55",
                  "display-flags":"-I/usr/local/boost-1.55.0/include",
                  "display-name":"Boost 1.55.0"
                }]
              },{
                "default":true,
                "name":"sprout",
                "display-flags":"-I/usr/local/sprout",
                "display-name":"Sprout"
              },{
                "default":"gnu++1y",
                "options":[{
                  "name":"c++98",
                  "display-flags":"-std=c++98 -pedantic",
                  "display-name":"C++03"
                },{
                  ...
                },{
                  "name":"gnu++1y",
                  "display-flags":"-std=gnu++1y",
                  "display-name":"C++1y(GNU)"
                }]
              }],
              "name":"gcc-head",
              "version":"4.9.0 20131031 (experimental)",
              "language":"C++",
              "display-name":"gcc HEAD"
              "templates":["gcc"]
            },{
              ...
            }]
        ```

        """
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        return await self._get(url=self.url.format("list.json"), headers=headers, **kwargs)

    async def get_permlink(self, link: str, **kwargs) -> typing.Dict[str, typing.Any]:
        """
        Requests the data of a prior compilation with the endpoint https://wandbox.org/api/permlink/:link

        :param link:    Identifier assigned by Wandbox. Completes end of API url
        :param kwargs:  Keyword arguments to modify aiohttp ClientSession().get() method
        :return:        Dictionary of compilation data
        """
        return await self._get(url=self.url.format(f"permlink/{link}"), **kwargs)

    async def get_template(self, name: str, **kwargs) -> str:
        """
        Requests a sample of code given a compiler name

        :param name:    Name of the compiler template
        :param kwargs:  Keyword arguments to modify aiohttp ClientSession().get() method
        :return:        String of code

        ```
        gcc_code = await Wandbox.get_template("gcc")
        gcc_code == "// This file is a \"Hello, world!\" in C++ language by gcc for wandbox.\n#include <iostream>\n#include <cstdlib>\n\nint main()\n{\n    std::cout << \"Hello, Wandbox!\" << std::endl;\n}\n\n// C++ language references:\n//   https://msdn.microsoft.com/library/3bstk3k5.aspx\n//   http://www.cplusplus.com/\n//   https://isocpp.org/\n//   http://www.open-std.org/jtc1/sc22/wg21/\n\n// Boost libraries references:\n//   http://www.boost.org/doc/\n"
        ```
        """
        code = await self._get(url=self.url.format(f"template/{name}"), **kwargs)
        return code['code'] if isinstance(code, dict) else code

    async def get_user(self, session: str, **kwargs) -> typing.Dict[str, typing.Any]:
        """
        Given a session, requests the user's login status and GitHub username

        :param session: Session identifier assigned by Wandbox
        :param kwargs:  Keyword arguments to modify aiohttp ClientSession().get() method
        :return:        Dictionary with 'login' and 'username' keys

        ```
        user = await Wandbox.get_user("zi35OwVNg0SwKMQo3VpfZeWxuXSyQ2nA")
        user == {"login":true,"username":"melpon"}
        ```
        """
        return await self._get(url=self.url.format("url.json"), data=json.dumps({'session': session}), **kwargs)

    async def compile(
            self,
            code: str,
            compiler: str,
            codes: typing.List[dict] = (),
            compiler_option_raw: bool = False,
            options: str = '',
            runtime_option_raw: bool = False,
            save: bool = False,
            stdin: str = '',
            **kwargs
    ):
        """
        Sends code to Wandbox to be compiled with the given parameters and returns the program's output.

        :param code:                Code to compile and execute
        :param compiler:            Compiler name as described by Wandbox
        :param codes:               List of supplementary code objects {'code': abcd..., 'file': 'demo.py'}
        :param compiler_option_raw: ...
        :param options:             Compiler options (as would be typed in terminal)
        :param runtime_option_raw:  ...
        :param save:                Create and return a permanent link to reference this compilation
        :param stdin:               Data to feed into input calls from running program
        :param kwargs:              Keyword arguments to modify aiohttp ClientSession().post() method
        :return:                    Dictionary
        """
        params = {
            'code': code,
            'codes': codes,
            'compiler': compiler,
            'compiler-option-raw': compiler_option_raw,
            'options': options,
            'runtime-option-raw': runtime_option_raw,
            'save': save,
            'stdin': stdin
        }

        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        # Must update kwargs to prevent conflicting arguments
        kwargs.update({'data': json.dumps(params), 'headers': headers})
        return await self._post(url=self.url.format("compile.json"), **kwargs)

    async def compile_nd(
            self,
            code: str,
            compiler: str,
            codes: typing.List[dict] = (),
            compiler_option_raw: typing.Any = '',
            options: str = '',
            runtime_option_raw: typing.Any = '',
            stdin: str = '',
            **kwargs
    ):
        """
        Sends code to Wandbox to be compiled with the given parameters and returns performance/completion dictionaries.

        :param code:                Code to compile and execute
        :param compiler:            Compiler name as described by Wandbox
        :param codes:               List of supplementary code objects {'code': abcd..., 'file': 'demo.py'}
        :param compiler_option_raw: ...
        :param options:             Compiler options (as would be typed in terminal)
        :param runtime_option_raw:  ...
        :param stdin:               Data to feed into input calls from running program
        :param kwargs:              Keyword arguments to modify aiohttp ClientSession().post() method
        :return:                    Requests.Response instance
        """
        params = {
            'code': code,
            'codes': codes,
            'compiler': compiler,
            'compiler-option-raw': compiler_option_raw,
            'options': options,
            'runtime-option-raw': runtime_option_raw,
            'stdin': stdin
        }

        headers = {'Content-type': 'application/x-ndjson', 'Accept': 'text/plain'}
        # Must update kwargs to prevent conflicting arguments
        kwargs.update({'data': json.dumps(params), 'headers': headers})
        return await self._post(url=self.url.format("compile.ndjson"), **kwargs)

    async def post_permlink(
            self,
            code: str,
            compiler: str,
            codes: typing.List[dict] = (),
            compiler_option_raw: str = '',
            options: str = '',
            results: typing.List[dict] = (),
            runtime_option_raw: str = '',
            stdin: str = '',
            **kwargs
    ):
        """
        Sends code to Wandbox to be compiled with the given parameters and returns the link and url

        :param code:                Code to compile and execute
        :param compiler:            Compiler name as described by Wandbox or Compiler object
        :param codes:               List of supplementary code objects {'code': abcd..., 'file': 'demo.py'}
        :param compiler_option_raw: ...
        :param options:             Compiler options (as would be typed in terminal)
        :param results:             List of nd JSON objects containing compile-time results
        :param runtime_option_raw:  ...
        :param stdin:               Data to feed into input calls from running program
        :param kwargs:              Keyword arguments to modify aiohttp ClientSession().get() method
        :return:                    Requests.Response instance
        """
        params = {
            'code': code,
            'codes': codes,
            'compiler': compiler,
            'compiler-option-raw': compiler_option_raw,
            'options': options,
            'results': results,
            'runtime-option-raw': runtime_option_raw,
            'stdin': stdin
        }
        # Must update kwargs to prevent conflicting arguments
        kwargs.update({'params': json.dumps(params)})
        return await self._post(url=self.url.format("permlink"), **kwargs)


@atexit.register
def _disconnect():
    """
    Closes active session
    :return:
    """

    async def shutdown():
        try:
            await asyncio.gather(*[s.close() for s in Wandbox.active])
        except Exception as e:
            raise

    asyncio.run(shutdown())
