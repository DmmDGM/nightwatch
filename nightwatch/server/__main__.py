# Copyright (c) 2024 iiPython

# Modules
import os
import asyncio
from http import HTTPStatus

from requests import Session
from requests.exceptions import RequestException
from websockets.http11 import Response
from websockets.asyncio.server import serve
from websockets.datastructures import Headers

from . import connection

from nightwatch import __version__
from nightwatch.logging import log

# Handle proxying images
SESSION = Session()
PROXY_SIZE_LIMIT = 10 * (1024 ** 2)
PROXY_ALLOWED_SUFFIX = ["avif", "avifs", "apng", "png", "jpeg", "jpg", "jfif", "webp", "ico", "gif", "svg"]

def proxy_handler(connection, request):
    if request.path != "/gateway":
        if not request.path.startswith("/proxy"):
            return connection.respond(HTTPStatus.NOT_FOUND, "Nightwatch: Specified content was not found.\n")

        url = request.path[6:].lstrip("/")
        if not (url.strip() and "." in url):
            return connection.respond(HTTPStatus.BAD_REQUEST, "Nightwatch: Specified URI is incorrect.\n")

        paths = url.split("/")
        if ".." in url or len(paths) < 2 or "." not in paths[-1] or paths[-1].split(".")[-1] not in PROXY_ALLOWED_SUFFIX:
            return connection.respond(HTTPStatus.BAD_REQUEST, "Nightwatch: Specified URI is incorrect.\n")

        log.info("proxy", f"Proxying to https://{url}")
        try:
            data = b""
            with SESSION.get(f"https://{url}", headers = {"User-Agent": request.headers.get("User-Agent", "")}, stream = True) as response:
                response.raise_for_status()
                for chunk in response.iter_content(PROXY_SIZE_LIMIT):
                    data += chunk
                    if len(data) >= PROXY_SIZE_LIMIT:
                        return connection.respond(HTTPStatus.BAD_REQUEST, "Nightwatch: Specified URI contains data above size limit.")

                return Response(response.status_code, "OK", Headers([
                    (k, v)
                    for k, v in response.headers.items() if k in ["Content-Type", "Content-Length", "Cache-Control"]
                ]), data)

        except RequestException:
            return connection.respond(HTTPStatus.BAD_REQUEST, "Nightwatch: Failed to contact the specified URI.")

# Entrypoint
async def main() -> None:
    host, port = os.getenv("HOST", "localhost"), int(os.getenv("PORT", 8000))
    log.info("ws", f"Nightwatch v{__version__} running on ws://{host}:{port}/")
    async with serve(connection, host, port, process_request = proxy_handler):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
