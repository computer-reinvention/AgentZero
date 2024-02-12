from typing import Callable
from tools import Tool


class ToolSet:
    """
    A class to group tools together.
    """

    def __init__(self, shared_kwargs: dict, tags: list[str]):
        self.shared_kwargs = shared_kwargs
        self.tags = tags
        self.tools = []
        self.tool_dict = {}

    def register(self, func: Callable):
        """
        Registers the function as a tool in the toolset and ensures it has access to the shared state.
        """

        def wrapper(*args, **kwargs):
            kwargs = kwargs | self.shared_kwargs
            return func(*args, **kwargs)

        wrapped_func = wrapper
        tool = Tool(func.__name__, wrapped_func)

        self.tools.append(tool)
        self.tool_dict[tool.name] = tool

        return wrapped_func
