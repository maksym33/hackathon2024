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

from cl.runtime import Context
from typing import Type
from cl.convince.entries.entry import Entry
from cl.convince.llms.gpt.gpt_llm import GptLlm
from cl.convince.retrievers.multiple_choice_retriever import MultipleChoiceRetriever
from cl.runtime.log.exceptions.user_error import UserError
from cl.tradeentry.entries.number_entry import NumberEntry

_PAY_FREQ = "Payment frequency in months, for example 3 for quarterly."


@dataclass(slots=True, kw_only=True)
class PayFreqMonthsEntry(Entry):
    """Maps payment frequency string specified by the user to number of months."""

    pay_freq_months: int | None = None
    """Payment frequency."""

    def get_base_type(self) -> Type:
        return PayFreqMonthsEntry

    def run_generate(self) -> None:
        """Retrieve parameters from this entry and save the resulting entries."""

        # TODO: Check if the entry already exists in DB

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
        options = ['1', '3', '6', '12']

        input_text = self.get_text()
        retrieval = retriever.retrieve(
            input_text=input_text,
            param_description=_PAY_FREQ,
            valid_choices=options,
        )

        pay_freq_months = NumberEntry(text=retrieval.param_value)
        pay_freq_months.run_generate()
        self.pay_freq_months = int(pay_freq_months.value)

        # Save self to DB
        Context.current().save_one(self)
