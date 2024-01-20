import json


class Format:
    """
    Utility class for formatting methods.
    """

    @classmethod
    def as_observation(cls, result):
        """
        Format the result of a tool call as observation for the Agent.
        """
        return (
            "```"
            + json.dumps(
                {
                    "type": "OBSERVATION",
                    "observation": result,
                }
            )
            + "```"
        )

    @classmethod
    def as_input(cls, input):
        """
        Format the result of a tool call as input for the Agent.
        """
        return (
            "```"
            + json.dumps(
                {
                    "type": "INPUT",
                    "input": input,
                }
            )
            + "```"
        )

    @classmethod
    def clean(cls, text: str) -> str:
        """
        Remove unwanted characters from the text.
        OpenAI API doesn't allow special characters or spaces in the name.
        """
        if text.isalnum():
            return text

        filtered_text = ""

        for char in text:
            if not (char.isalnum() or char in ("_", " ")):
                continue

            if char == " ":
                filtered_text += "_"
            else:
                filtered_text += char

        if not filtered_text:
            return "User"

        return filtered_text
