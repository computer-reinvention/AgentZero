"""
Tools for interacting with calendar and email client.
"""
import inspect
from typing import Callable


class Tool:
    """
    Tool wrapper that attaches metadata to a function to be used
    by the agent based on it's docstring and name.
    """

    def __init__(self, name: str, function: Callable):
        """
        Args:
        name: str - Name given to this tool.
        function: Callable - The function to be used
        """
        self.name = name
        self.doc = function.__doc__

        if self.doc is None:
            raise ValueError(f"Function {self.name} has no docstring.")

        self.signature = str(inspect.signature(function))
        self.function = function

    def __str__(self):
        fun = f"{self.name}{self.signature}"
        return f"Tool: {fun}\nDescription: {self.doc}\n"

    def run(self, **kwargs):
        return self.function(**kwargs)


class ToolResponseType:
    """
    Flag indicating whether the agent should stop or continue.
    Useful for controlling from inside the tool if it's
    return should become the final output for this run.
    """

    CHAIN = 0
    RETURN = 1


class ToolResponse:
    """
    Class representing the response from the tool.
    Additional metadata can be attached to the response
    and passed around between tools.
    """

    def __init__(self, type: int, response: str = "", data={}):
        self.type = type
        self.response = response
        self.data = data
