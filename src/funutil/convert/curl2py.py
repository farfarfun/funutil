# -*- coding: utf-8 -*-
"""
source : https://github.com/spulec/uncurl
"""

import argparse
import json
import re
import shlex
from collections import OrderedDict, namedtuple

from six.moves import http_cookies as Cookie

parser = argparse.ArgumentParser()
parser.add_argument("command")
parser.add_argument("url")
parser.add_argument("-d", "--data")
parser.add_argument("-b", "--data-binary", "--data-raw", default=None)
parser.add_argument("-X", default="")
parser.add_argument("-H", "--header", action="append", default=[])
parser.add_argument("--compressed", action="store_true")
parser.add_argument("-k", "--insecure", action="store_true")
parser.add_argument("--user", "-u", default=())
parser.add_argument("-i", "--include", action="store_true")
parser.add_argument("-s", "--silent", action="store_true")
parser.add_argument("-x", "--proxy", default={})
parser.add_argument("-U", "--proxy-user", default="")

BASE_INDENT = " " * 4

ParsedContext = namedtuple(
    "ParsedContext",
    ["method", "url", "data", "headers", "cookies", "verify", "auth", "proxy"],
)


def normalize_newlines(multiline_text):
    return multiline_text.replace(" \\\n", " ")


def parse_context(curl_command):
    tokens = shlex.split(normalize_newlines(curl_command))
    parsed_args = parser.parse_args(tokens)
    post_data = parsed_args.data or parsed_args.data_binary

    method = "post" if post_data else "get"
    if parsed_args.X:
        method = parsed_args.X.lower()

    cookie_dict = OrderedDict()
    quoted_headers = OrderedDict()

    for curl_header in parsed_args.header:
        if curl_header.startswith(":"):
            occurrence = [m.start() for m in re.finditer(":", curl_header)]
            header_key, header_value = (
                curl_header[: occurrence[1]],
                curl_header[occurrence[1] + 1 :],
            )
        else:
            header_key, header_value = curl_header.split(":", 1)

        if header_key.lower().strip("$") == "cookie":
            cookie = Cookie.SimpleCookie(
                bytes(header_value, "ascii").decode("unicode-escape")
            )
            for key in cookie:
                cookie_dict[key] = cookie[key].value
        else:
            quoted_headers[header_key] = header_value.strip()

    # add auth
    user = parsed_args.user
    if parsed_args.user:
        user = tuple(user.split(":"))

    # add proxy and its authentication if it's available.
    proxies = parsed_args.proxy
    # proxy_auth = parsed_args.proxy_user
    if parsed_args.proxy and parsed_args.proxy_user:
        proxies = {
            "http": f"http://{parsed_args.proxy_user}@{parsed_args.proxy}/",
            "https": f"http://{parsed_args.proxy_user}@{parsed_args.proxy}/",
        }
    elif parsed_args.proxy:
        proxies = {
            "http": f"http://{parsed_args.proxy}/",
            "https": f"http://{parsed_args.proxy}/",
        }

    return ParsedContext(
        method=method,
        url=parsed_args.url,
        data=post_data,
        headers=quoted_headers,
        cookies=cookie_dict,
        verify=parsed_args.insecure,
        auth=user,
        proxy=proxies,
    )


def convert_curl_to_python(curl_command, **kwargs):
    parsed_context = parse_context(curl_command)

    data_token = ""
    if parsed_context.data:
        data_token = f"{BASE_INDENT}data='{parsed_context.data}',\n"

    verify_token = ""
    if parsed_context.verify:
        verify_token = f"\n{BASE_INDENT}verify=False"

    requests_kwargs = ""
    for k, v in sorted(kwargs.items()):
        requests_kwargs += f"{BASE_INDENT}{k}={v},\n"

    auth_data = f"{BASE_INDENT}auth={parsed_context.auth}"
    proxy_data = f"\n{BASE_INDENT}proxies={parsed_context.proxy}"

    formatter = {
        "method": parsed_context.method,
        "url": parsed_context.url,
        "data_token": data_token,
        "headers_token": f"{BASE_INDENT}headers={dict_to_pretty_string(parsed_context.headers)}",
        "cookies_token": f"{BASE_INDENT}cookies={dict_to_pretty_string(parsed_context.cookies)}",
        "security_token": verify_token,
        "requests_kwargs": requests_kwargs,
        "auth": auth_data,
        "proxies": proxy_data,
    }

    return """requests.{method}("{url}",
{requests_kwargs}{data_token}{headers_token},
{cookies_token},
{auth},{proxies},{security_token}
)""".format(**formatter)


def dict_to_pretty_string(the_dict, indent=4):
    if not the_dict:
        return "{}"

    return ("\n" + " " * indent).join(
        json.dumps(
            the_dict, sort_keys=True, indent=indent, separators=(",", ": ")
        ).splitlines()
    )
