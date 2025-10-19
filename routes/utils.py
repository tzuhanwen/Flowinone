from typing import Callable, Iterable, Any
from functools import partial
from flask import Flask


def register_routes(app: Flask, route_handlers: Iterable[tuple[str, Callable]]) -> None:
    for endpoint_str, handler in route_handlers:
        app.route(endpoint_str)(handler)


class RouteRegistry:
    routes: list[tuple[str, Callable[..., Any]]]

    def __init__(self) -> None:
        self.routes = []

    def register(self, route_str: str) -> Callable[[Callable[..., Any]], None]:
        return partial(self._append_to_registry, route_str)

    def _append_to_registry(self, route_str: str, handler: Callable[..., Any]) -> None:
        self.routes.append((route_str, handler))
