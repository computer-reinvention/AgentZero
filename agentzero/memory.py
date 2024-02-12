from agentzero.utils import Message


class WorkingMemory:
    """
    Working memeory for a single Agent run.
    Stores the evaluations of consecutive tool calls for a single run.
    """

    def __init__(self, messages: list[Message]):
        self.messages = messages
        self.dict_messages = [message.__dict__() for message in messages]

    def commit(self, messages):
        self.messages.extend(messages)
        self.dict_messages.extend([message.__dict__() for message in messages])
