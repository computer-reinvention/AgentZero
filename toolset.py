from typing import Callable
from tools import Tool


class ToolSet:
    """
    A class to group tools together.
    """

    def __init__(self, tags: list[str]):
        self.tags = tags
        self.tools = []
        self.tool_dict = {}

    def register(self, func: Callable):
        """
        Registers the function as a tool in the toolset.
        """
        tool = Tool(func.__name__, func)

        self.tools.append(tool)
        self.tool_dict[tool.name] = tool

        return func
