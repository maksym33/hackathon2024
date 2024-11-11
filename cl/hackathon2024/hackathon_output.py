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

from cl.hackathon2024.hackathon_output_key import HackathonOutputKey
from cl.runtime import RecordMixin
from cl.runtime.records.dataclasses_extensions import missing


@dataclass(slots=True, kw_only=True)
class HackathonOutput(HackathonOutputKey, RecordMixin[HackathonOutputKey]):
    """Output fields for a single hackathon trade obtained using the specified solution."""

    entry_text: str = missing()
    """Trade entry text for the specified trade."""

    score_pct: float | None = None
    """Ratio of correct outputs expressed in percent."""

    notional_amount: float | None = None
    """Notional amount of the swap."""

    notional_currency: str | None = None  # TODO: schedule
    """Currency of the notional amount."""

    effective_date: str | None = None
    """Effective date in ISO-8601 yyyy-mm-dd string format."""

    maturity_date: str | None = None
    """Maturity date in ISO-8601 yyyy-mm-dd string format."""

    leg_1_float_freq: str | None = None
    """Frequency at which floating interest accrues."""

    leg_1_float_index: str | None = None
    """Floating interest rate index ('float_spread' is added to the index fixing)."""

    leg_1_float_spread_bp: float | None = None
    """Spread over the interest rate index in basis points."""

    leg_1_fixed_rate_pct: float | None = None
    """Fixed rate in percent."""

    leg_1_pay_receive: str | None = None
    """Flag indicating if we pay or receive payments or periodic coupons for a trade or leg. 
    Values 'Pay' or 'Receive'."""

    leg_1_pay_freq: str | None = None
    """Payment frequency."""  # TODO: Specify format

    leg_2_float_freq: str | None = None
    """Frequency at which floating interest accrues."""

    leg_2_float_index: str | None = None
    """Floating interest rate index ('float_spread' is added to the index fixing)."""

    leg_2_float_spread_bp: float | None = None
    """Spread over the interest rate index in basis points."""

    leg_2_fixed_rate_pct: float | None = None
    """Fixed rate in percent."""

    leg_2_pay_receive: str | None = None
    """Flag indicating if we pay or receive payments or periodic coupons for a trade or leg. 
    Values 'Pay' or 'Receive'."""

    leg_2_pay_freq: str | None = None
    """Payment frequency."""  # TODO: Specify format

    def get_key(self) -> HackathonOutputKey:
        return HackathonOutputKey(solution=self.solution, trade_id=self.trade_id)
