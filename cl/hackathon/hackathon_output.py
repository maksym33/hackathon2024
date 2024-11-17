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
from typing import List
from cl.runtime import Context
from cl.runtime import RecordMixin
from cl.runtime.records.dataclasses_extensions import missing
from cl.convince.retrievers.annotating_retrieval import AnnotatingRetrieval
from cl.hackathon.hackathon_output_key import HackathonOutputKey


@dataclass(slots=True, kw_only=True)
class HackathonOutput(HackathonOutputKey, RecordMixin[HackathonOutputKey]):
    """Output fields for a single hackathon trade obtained using the specified solution."""

    entry_text: str = missing()
    """Trade entry text for the specified trade."""

    effective_date: str | None = None
    """Effective date in ISO-8601 yyyy-mm-dd format (omit if not specified)."""

    maturity_date: str | None = None
    """Maturity date in ISO-8601 yyyy-mm-dd string format (omit if not specified)."""

    tenor_years: str | None = None
    """Tenor in whole years, for example 10 for a 10 year swap (omit if not specified)."""

    pay_leg_notional: str | None = None
    """Pay leg notional amount."""

    pay_leg_ccy: str | None = None
    """Pay leg payment currency in 3-letter ISO-4217 format, for example USD."""

    pay_leg_freq_months: str | None = None
    """Pay leg payment frequency in months, for example 3."""

    pay_leg_basis: str | None = None
    """Pay leg day-count basis as specified, for example actual/360."""

    pay_leg_float_index: str | None = None
    """Pay leg floating interest rate index as specified, e.g., '3m Term SOFR' (omit for a fixed leg)."""

    pay_leg_float_spread_bp: str | None = None
    """Pay leg spread in basis points, for example 30 (omit for a fixed leg, 0 or omit if not specified)."""

    pay_leg_fixed_rate_pct: str | None = None
    """Pay leg fixed rate in percent, for example 3.45 (omit for a floating leg)."""

    rec_leg_notional: str | None = None
    """Receive leg notional amount, for example 10000000."""

    rec_leg_ccy: str | None = None
    """Receive leg payment currency in 3-letter ISO-4217 format, for example USD."""

    rec_leg_freq_months: str | None = None
    """Pay leg payment frequency in months, for example 3."""

    rec_leg_basis: str | None = None
    """Pay leg day-count basis as specified, for example actual/360."""

    rec_leg_float_index: str | None = None
    """Receive leg floating interest rate index as specified, e.g., '3m Term SOFR' (omit for a fixed leg)."""

    rec_leg_float_spread_bp: str | None = None
    """Receive leg spread in basis points, for example 30 (omit for a fixed leg, 0 or omit if not specified)."""

    rec_leg_fixed_rate_pct: str | None = None
    """Receive leg fixed rate in percent (omit for a floating leg)."""

    def get_key(self) -> HackathonOutputKey:
        return HackathonOutputKey(
            solution=self.solution,
            trade_group=self.trade_group,
            trade_id=self.trade_id,
            trial_id=self.trial_id,
        )

    def view_detailed_information(self) -> List[AnnotatingRetrieval]:
        """Return the list of used annotating retrievals."""
        context = Context.current()

        current_retriever_id = (
            f"{self.solution.solution_id}::{self.trade_group}::{self.trade_id}::{self.trial_id}"
        )
        retrievals = context.load_all(AnnotatingRetrieval)
        filtered_retrievals = [
            retrieval for retrieval in retrievals if retrieval.retriever.retriever_id == current_retriever_id
        ]

        return filtered_retrievals
