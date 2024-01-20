"""
Parsers and other utilities.
"""
from typing import Any

import openai
import demjson3


JSON_FIX_PROMPT = """Fix the broken JSON syntax in the following blobs:
###BROKEN###
{
    "id": "bdsfhsdfjioejfrelfhoieruwpor",
    "name": "David,

}
###FIXED###
{
    "id": "bdsfhsdfjioejfrelfhoieruwpor",
    "name": "David"
}
###END###

###BROKEN###
{blob}
###FIXED###"""


def correcting_json_parser(blob: str) -> dict[str, Any] | None:
    """
    Try to parse a json blob using demjson3. If
    If there are formatting errors, it uses GPT-3 to try to fix them.
    """
    try:
        res = demjson3.decode(blob)
        return dict(res)
    except demjson3.JSONDecodeError:
        pass

    try:
        res = openai.completions.create(
            model="gpt-3.5-turbo-instruct",
            prompt=JSON_FIX_PROMPT.replace("{blob}", blob),
            max_tokens=512,
            stop=["###END###"],
            temperature=0.1,
            best_of=1,
        )
    except Exception as exc:
        print("Exception is correcting JSON parser : ", exc)
        return None

    corrected = res.choices[0].text.strip(" ").strip("\n")

    try:
        res = demjson3.decode(corrected)
        return dict(res)
    except demjson3.JSONDecodeError:
        return None
