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
from typing import Dict, List

from cl.convince.llms.gpt.gpt_llm import GptLlm
from cl.convince.prompts.formatted_prompt import FormattedPrompt
from cl.convince.retrievers.annotating_retriever import AnnotatingRetriever
from cl.convince.retrievers.retrieval import Retrieval
from cl.hackathon.hackathon_input import HackathonInput
from cl.hackathon.hackathon_output import HackathonOutput
from cl.hackathon.hackathon_solution_key import HackathonSolutionKey
from cl.hackathon.hackathon_trade_list_key import HackathonTradeListKey
from cl.runtime import Context, RecordMixin
from cl.runtime.log.exceptions.user_error import UserError
from cl.tradeentry.entries.amount_entry import AmountEntry
from cl.tradeentry.entries.currency_entry import CurrencyEntry
from cl.tradeentry.entries.date_entry import DateEntry
from cl.tradeentry.entries.date_or_tenor_entry import DateOrTenorEntry
from cl.tradeentry.entries.number_entry import NumberEntry
from cl.tradeentry.entries.pay_freq_entry import PayFreqEntry
from cl.tradeentry.entries.pay_receive_entry import PayReceiveEntry
from cl.tradeentry.entries.rates.rates_index_entry import RatesIndexEntry
from cl.tradeentry.entries.rates.swaps.any_leg_entry import AnyLegEntry
from cl.tradeentry.entries.rates.swaps.rates_swap_entry import RatesSwapEntry
from cl.runtime.records.dataclasses_extensions import missing
from cl.tradeentry.trades.currency_key import CurrencyKey
from cl.tradeentry.entries.trade_entry import TradeEntry
from cl.tradeentry.trades.trade_key import TradeKey


@dataclass(slots=True, kw_only=True)
class HackathonSolution(HackathonSolutionKey, RecordMixin[HackathonSolutionKey]):
    """Define parameters to convert trade entry text to the trade and perform scoring."""

    trade_list: HackathonTradeListKey | None = None
    """List of trades for which scoring will be performed (optional, will score all trades if not specified)."""

    score_pct: float | None = None
    """Score in percent for the specified trade list."""

    def get_key(self) -> HackathonSolutionKey:
        return HackathonSolutionKey(solution_id=self.solution_id)

    def init(self) -> None:
        """Same as __init__ but can be used when field values are set both during and after construction."""

    def view_inputs(self) -> List[HackathonInput]:
        """Return the list of inputs specified by the trade list."""

    def view_outputs(self) -> List[HackathonInput]:
        """Return the list of outputs (each with its score)."""
