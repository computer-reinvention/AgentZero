import traceback
import pprint
import openai
import pendulum

from agentzero.format import Format
from agentzero.memory import WorkingMemory
from agentzero.parser import correcting_json_parser
from agentzero.templates import SYS_PROMPT_USR
from agentzero.tools import Tool, ToolResponse, ToolResponseType
from agentzero.utils import ChatRoles, Message


class Agent:
    def __init__(
        self,
        model: str = "gpt-4-1106-preview",
        max_iter: int = 2,
        temperature: float = 0.2,
        tools: list[Tool] = [],
    ):
        self.MODEL = model
        self.MAX_ITER = max_iter
        self.tools = tools
        self.current_input = None
        self.tool_dict = {tool.name: tool for tool in tools}
        self.memory = WorkingMemory([])
        self.temperature = temperature

    def _initialize_memory(self):
        """
        Initialize the working memory for this run.
        """
        print("Agent._initialize_memory()")
        content = SYS_PROMPT_USR.replace(
            "{current_time}",
            pendulum.now("Asia/Kolkata").to_day_datetime_string(),
        ).replace("{tools}", "\n".join([str(tool) for tool in self.tools]))

        print("\n\n====== System Prompt =======")
        print(content)
        print("============================\n\n")

        self.memory.commit(
            [
                Message(
                    name="Sys",
                    role=ChatRoles.SYS,
                    content=content,
                ),
                Message(
                    name=Format.clean(""),
                    role=ChatRoles.USR,
                    content=Format.as_input(self.current_input),
                ),
            ]
        )

    def _llm_call(self, error="", faulty_comp="") -> str:
        """
        Call the API with system prompt and history.
        """
        print("Agent._llm_call()")

        if error:
            self.memory.commit(
                [
                    Message("Mavy", ChatRoles.AI, faulty_comp),
                    Message("sys", ChatRoles.SYS, error),
                ]
            )

        try:
            res = openai.chat.completions.create(
                model=self.MODEL,
                messages=self.memory.dict_messages,
                temperature=self.temperature,
            )
        except Exception as exc:
            print("Exception in API Call : ", exc)
            return ""

        print("==================")
        print("== API Response ==")
        print("==================")
        pprint.pprint(res)
        print("==================")

        reply = res.choices[0].message.content

        return str(reply)

    def _think(self) -> tuple[str | None, dict | None]:
        """
        Process the resulting JSON blob from api call into a dict.
        Automatically retry with specifying the problem if an parsing error occurs.
        """
        print("Agent._think()")
        parsed = False
        counter = 0
        comp = ""
        error = ""
        parsed_result = None

        FIX_PREV_RESPONSE = (
            "Your previous response {problem}."
            "Please repeat your response exactly but with the errors fixed."
        )

        while not parsed and counter < 3:
            comp = self._llm_call(error, comp)
            error = ""

            # ensure the response is a JSON blob
            if "```" not in comp:
                print("Wrong format. Asking to fix.")
                error = FIX_PREV_RESPONSE.format(
                    problem="did not adhere to the prescribed output format"
                )
                counter = counter + 1
                continue

            # ensure we can parse the response
            try:
                parsed_result = correcting_json_parser(
                    comp.strip("\n").strip("```")
                )
            except Exception as exc:
                print("Exception while parsing. Asking to fix.")
                error = FIX_PREV_RESPONSE.format(
                    problem=(
                        "was improperly formatted JSON. "
                        "The exact python exception raised was : "
                        + str(exc)
                        + "\nPlease repeat the same response without the errors. Do not mention this error in your response."
                    )
                )
                print(error)
                counter = counter + 1
                continue

            thought = parsed_result.get("thought")
            action = parsed_result.get("action")

            if thought is None:
                print("Thought is null. Asking to fix.")
                error = FIX_PREV_RESPONSE.format(
                    problem="the thought key is None. Please repeat with an appropriate and concise thought."
                )
                counter = counter + 1
                continue

            # ensure both are not None at the same time
            if action is None:
                print("Action is null. Asking to fix.")
                error = FIX_PREV_RESPONSE.format(
                    problem="the action key is None. Please repeat with an appropriate value for the action, or the FINAL_ANSWER flag."
                )
                counter = counter + 1
                continue

            action_name = action.get("name")
            action_args = action.get("args")

            if action_name is None:
                print("Action Name is null. Asking to fix.")
                error = FIX_PREV_RESPONSE.format(
                    problem="the action name key is None. Please repeat with an appropriate value for the action name, or the FINAL_ANSWER flag."
                )
                counter = counter + 1
                continue

            if action_args is None:
                parsed_result["action"]["args"] = {}

            parsed = True

        return comp, parsed_result

    def _do(self, action_name: str, action_args: dict):
        """
        Take actions or create replies based on the result of self._think.
        """
        print("Agent._do()")

        terminate = False
        error = False

        if action_name == "FINAL_ANSWER":
            terminate = True
            error = False
            return (terminate, error, action_args["content"])

        if action_name in self.tool_dict:
            print("Action : ", action_name)
            tool = self.tool_dict[action_name]
            try:
                res = tool.run(**action_args)

                print("Action Result : ", res)

                if isinstance(res, ToolResponse):
                    if res.type == ToolResponseType.RETURN:
                        terminate = True
                        error = False
                        return (terminate, error, res.response)

                    res = res.response

            except Exception as exc:
                traceback.print_exc()
                terminate = False
                error = True
                return (
                    terminate,
                    error,
                    f"Error while executing tool : {str(exc)}",
                )

            terminate = False
            error = False
            return (terminate, error, res)

        terminate = False
        error = True

        return (
            terminate,
            error,
            f"{action_name} is not a valid action or tool.",
        )

    def _runner(self):
        """
        Run the Thought-Observation-Action cycle.
        """
        print("Agent._runner()")
        terminate = False
        error = False
        reply = None

        i: int = 0
        while (i <= self.MAX_ITER) and not terminate:
            comp, res = self._think()

            if res is None:
                raise ValueError(
                    "Result of thinking cannot be None. "
                    "Artificial stupidity."
                )

            self.memory.commit(
                [
                    Message(
                        "Assistant",
                        ChatRoles.AI,
                        comp,
                    )
                ]
            )

            action_name = res["action"]["name"]
            action_args = res["action"]["args"]

            terminate, error, reply = self._do(action_name, action_args)

            if terminate:
                break

            if error:
                self.memory.commit(
                    [
                        Message(
                            "sys",
                            ChatRoles.SYS,
                            f"Your above action resulted in this error : '{reply}'. "
                            "Please fix your response.",
                        ),
                    ]
                )
                continue

            self.memory.commit(
                [
                    Message(
                        action_name,
                        ChatRoles.USR,
                        Format.as_observation(reply),
                    )
                ]
            )

        return reply

    def run(self, input):
        """
        Start the agent execution loop. During this loop, the agent may call tools to reach a result.
        """
        print("Agent.run()")
        self.current_input = input
        self._initialize_memory()

        if self.current_input is None:
            raise ValueError("User input cannot be None.")

        return self._runner()
