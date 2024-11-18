# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from dataclasses import dataclass
from typing import Type
from typing_extensions import Self
from cl.runtime import Context
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.records.dataclasses_extensions import missing
from cl.convince.entries.entry import Entry
from cl.convince.entries.entry_key import EntryKey
from cl.convince.llms.gpt.gpt_llm import GptLlm
from cl.convince.llms.llm import Llm
from cl.convince.retrievers.retriever_util import RetrieverUtil
from cl.tradeentry.entries.rates.swaps.fixed_swap_leg_entry import FixedSwapLegEntry
from cl.tradeentry.entries.rates.swaps.float_swap_leg_entry import FloatSwapLegEntry

_PROMPT_TEMPLATE = """You will be given the input below in the form of description of trade entry leg.

Return only JSON with following keys:
* LegType - enum with values Floating and Fixed

Description of trade entry leg:
```
{input_text}
```"""


@dataclass(slots=True, kw_only=True)
class AnyLegEntry(Entry):
    """Capture any leg type from user input, leg type is determined from the input."""

    leg: EntryKey | None = None
    """Entry for the leg."""

    max_retries: int = missing()
    """How many times to retry the annotation in case changes other than braces are detected."""

    def get_base_type(self) -> Type:
        return AnyLegEntry

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""

        # Default max_retries
        if self.max_retries is None:
            self.max_retries = 1

        # Return self to enable method chaining
        return self

    def determine_leg_type(self, leg_type_prompt: str) -> str | None:
        """Determine leg type, after which this record will be replaced by a record of this type."""

        # Load the full LLM specified by the context
        context = Context.current()
        llm = context.load_one(Llm, context.full_llm)

        input_text = self.text
        for retry_index in range(self.max_retries):
            is_last_trial = retry_index == self.max_retries - 1

            # Append retry_index to trial_id to avoid reusing a cached completion
            if self.max_retries > 1:
                context = Context.current()
                if context.trial is not None:
                    trial_key = TrialKey(trial_id=f"{context.trial.trial_id}\\{retry_index}")
                else:
                    trial_key = TrialKey(trial_id=str(retry_index))
            else:
                trial_key = context.trial
            with Context(trial=trial_key) as context:

                try:
                    # Create a brace extraction prompt using input parameters
                    rendered_prompt = leg_type_prompt.format(input_text=input_text)

                    # Run completion
                    completion = llm.completion(rendered_prompt)

                    # Extract the results
                    json_result = RetrieverUtil.extract_json(completion)
                    if json_result is not None:
                        leg_type = json_result.get("LegType", None)
                        if leg_type != "Fixed" and leg_type != "Floating":
                            raise UserError(f"Undefined leg type: {leg_type}")

                    else:
                        raise UserError(
                            f"Could not extract JSON from the LLM response. " f"LLM response:\n{completion}\n"
                        )

                    return leg_type

                except Exception as e:
                    if is_last_trial:
                        # Rethrow only when the last trial is reached
                        raise UserError(
                            f"Unable to extract parameter from the input text after {trial_count} trials.\n"
                            f"Input text: {input_text}\n"
                            f"Last trial error information: {str(e)}\n"
                        )
                    else:
                        # Otherwise continue
                        pass

        # The method should always return from the loop, adding as a backup in case this changes in the future
        raise UserError(f"Unable to extract parameter from the input text.\n" f"Input text: {input_text}\n")

    def run_generate(self) -> None:
        """Determine the leg type from the input and create an object of the corresponding type."""

        # Reset before regenerating to prevent stale field values
        self.run_reset()

        leg_type = self.determine_leg_type(_PROMPT_TEMPLATE)

        if leg_type == "Floating":
            leg_obj = FloatSwapLegEntry(text=self.text)
        elif leg_type == "Fixed":
            leg_obj = FixedSwapLegEntry(text=self.text)
        else:
            raise UserError(f"Undefined leg type: {leg_type}")

        leg_obj.run_generate()
        self.leg = leg_obj.get_key()

        Context.current().save_one(leg_obj)
        Context.current().save_one(self)
