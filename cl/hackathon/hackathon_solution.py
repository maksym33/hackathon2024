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
from cl.hackathon.hackathon_input import HackathonInput
from cl.hackathon.hackathon_solution_key import HackathonSolutionKey
from cl.hackathon.hackathon_trade_group_key import HackathonTradeGroupKey


@dataclass(slots=True, kw_only=True)
class HackathonSolution(HackathonSolutionKey, RecordMixin[HackathonSolutionKey]):
    """Define parameters to convert trade entry text to the trade and perform scoring."""

    trade_group: HackathonTradeGroupKey = missing()
    """Trade group for which scoring will be performed."""

    trade_ids: str | None = None
    """
    Dash- and comma-delimited list of trade ids to limit scoring within the group (optional).
    
    Notes:
        All trades in the group will scored if not specified
        Example: for '1-3, 5' only trades with id 1, 2, 3, 5 will be scored
    """

    def get_key(self) -> HackathonSolutionKey:
        return HackathonSolutionKey(solution_id=self.solution_id)

    def init(self) -> None:
        """Same as __init__ but can be used when field values are set both during and after construction."""

    def view_inputs(self) -> List[HackathonInput]:
        """Return the list of inputs specified by the trade list."""

    def view_outputs(self) -> List[HackathonInput]:
        """Return the list of outputs (each with its score)."""

    def get_trade_ids_list(self) -> List[int]:
        """Return the list of trade ids from the trade_ids string."""
        if not self.trade_ids:
            return []

        result = set()
        parts = self.trade_ids.split(',')

        for part in parts:
            part = part.strip()
            # Check if the part is a range like "1-3"
            if '-' in part:
                start, end = sorted([int(range_part) for range_part in part.split('-')])
                # Add the range of numbers to the result
                result.update(range(start, end + 1))
                continue

            # Add single number to the result
            result.add(int(part))

        return sorted(list(result))
