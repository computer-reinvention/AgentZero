"""
File demonstrating the agent and toolset.
"""

import pprint
import requests

from agentzero.agent import Agent
from agentzero.toolset import ToolSet

toolset = ToolSet(["testing"])


@toolset.register
def execute(code: str) -> str:
    """
    A function that evaluates arbitrary python code at runtime using exec().
    Be sure to assign results of your computation to a variable called "RES".
    Only the value inside "RES" will be returned as a string.
    """
    exec(code, globals(), locals())

    return locals()["RES"]


def main():
    """
    Main function that will initialize and execute the agent.
    """

    print("\n\n======= Tools ========")
    pprint.pprint(toolset.tools)
    print("=======================\n\n")

    agent = Agent(tools=toolset.tools, max_iter=10)

    res = agent.run(
        """1. Find out details about your current working directory - which contains your source code.
2. Examine the contents of test.py.
3. Create a copy of test.py but replace the instructions in main() with something funny (non-destructive).
4. Run another instance of yourself and observer it's behaviour.
5. Report your findings."""
    )

    print("\n\n======= Answer ========")
    print(res)
    print("=======================\n\n")


if __name__ == "__main__":
    main()
