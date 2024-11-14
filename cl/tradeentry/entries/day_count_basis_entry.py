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
from cl.runtime import Context
from cl.runtime.log.exceptions.user_error import UserError
from cl.convince.entries.entry import Entry
from cl.convince.llms.gpt.gpt_llm import GptLlm
from cl.convince.retrievers.multiple_choice_retriever import MultipleChoiceRetriever

_BASIS = "Day count basis"


@dataclass(slots=True, kw_only=True)
class DayCountBasisEntry(Entry):
    """Maps a date string specified by the user to a calendar date."""

    basis: str | None = None

    def get_base_type(self) -> Type:
        return DayCountBasisEntry

    def run_generate(self) -> None:
        """Retrieve parameters from this entry and save the resulting entries."""
        if self.verified:
            raise UserError(
                f"Entry {self.entry_id} is marked as verified, run Unmark Verified before running Propose."
                f"This is a safety feature to prevent overwriting verified entries. "
            )
        # Get retriever
        # TODO: Make configurable
        retriever = MultipleChoiceRetriever(
            retriever_id="MultipleChoiceRetriever",
            llm=GptLlm(llm_id="gpt-4o"),
        )
        retriever.init_all()

        # List of valid options
        # TODO: Not fixed list
        options = ["30/360", "30/365", "actual/360", "actual/365", "actual/actual"]

        input_text = self.get_text()
        retrieval = retriever.retrieve(
            input_text=input_text,
            param_description=_BASIS,
            valid_choices=options,
        )

        self.basis = retrieval.param_value

        # Save self to DB
        Context.current().save_one(self)
