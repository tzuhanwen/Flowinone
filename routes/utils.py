from typing import Callable, Iterable

from flask import Flask

def register_routes(app: Flask, route_handlers: Iterable[tuple[str, Callable]]) -> None:

    for endpoint_str, handler in route_handlers:
        app.route(endpoint_str)(handler)
