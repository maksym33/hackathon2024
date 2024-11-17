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

from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Final, Tuple
from typing_extensions import Self

from cl.hackathon.hackathon_input import HackathonInput
from cl.hackathon.hackathon_scoring_statistics import HackathonScoringStatistics
from cl.runtime import Context
from cl.runtime import RecordMixin
from cl.runtime import View
from cl.runtime.plots.heat_map_plot import HeatMapPlot
from cl.runtime.primitive.case_util import CaseUtil
from cl.hackathon.hackathon_input_key import HackathonInputKey
from cl.hackathon.hackathon_output import HackathonOutput
from cl.hackathon.hackathon_output_key import HackathonOutputKey
from cl.hackathon.hackathon_score_item import HackathonScoreItem
from cl.hackathon.hackathon_scoring_key import HackathonScoringKey
from cl.hackathon.hackathon_solution_key import HackathonSolutionKey
from cl.tradeentry.entries.date_entry import DateEntry
from cl.tradeentry.entries.number_entry import NumberEntry

COMPARE_AS_NUMBER_FIELDS: Final[Tuple] = ("tenor_years", "pay_leg_notional", "pay_leg_freq_months",
                                          "pay_leg_float_spread_bp", "pay_leg_fixed_rate_pct", "rec_leg_notional",
                                          "rec_leg_freq_months", "rec_leg_float_spread_bp", "rec_leg_fixed_rate_pct")

ERROR_KEYWORDS: Final[Tuple] = ("error", "escalation", "?")


@dataclass(slots=True, kw_only=True)
class HackathonScoring(HackathonScoringKey, RecordMixin[HackathonScoringKey]):
    """Class to perform scoring for hackathon solution."""

    trial_count: int | None = None
    """Number of trials for each input."""

    score: float | None = None
    """Total score for hackathon solution."""

    max_score: int | None = None
    """Maximum possible score for solution."""

    def get_key(self):
        return HackathonScoringKey(solution=self.solution)

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""
        if self.trial_count is None:
            self.trial_count = 1

        # Return self to enable method chaining
        return self
