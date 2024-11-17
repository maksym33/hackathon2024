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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from typing_extensions import Self

from cl.convince.llms.llm_key import LlmKey
from cl.runtime import Context
from cl.runtime import RecordMixin
from cl.runtime.records.dataclasses_extensions import missing
from cl.hackathon.hackathon_input import HackathonInput
from cl.hackathon.hackathon_output import HackathonOutput
from cl.hackathon.hackathon_scoring import HackathonScoring
from cl.hackathon.hackathon_scoring_key import HackathonScoringKey
from cl.hackathon.hackathon_solution_key import HackathonSolutionKey


@dataclass(slots=True, kw_only=True)
class HackathonSolution(HackathonSolutionKey, RecordMixin[HackathonSolutionKey], ABC):
    """Define parameters to convert trade entry text to the trade and perform scoring."""

    llm: LlmKey = missing()
    """LLM that will be used to generate the output."""

    trade_group: str = missing()
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

    def init(self) -> Self:
        """Similar to __init__ but can use fields set after construction, return self to enable method chaining."""
        # Save scoring object if does not exist
        solution_key = self.get_key()
        scoring_key = HackathonScoringKey(solution=solution_key)
        if Context.current().load_one(HackathonScoring, scoring_key, is_record_optional=True) is None:
            scoring_obj = HackathonScoring(solution=solution_key)
            Context.current().save_one(scoring_obj)

        # Return self to enable method chaining
        return self

    def view_inputs(self) -> List[HackathonInput]:
        """Return the list of inputs specified by the trade list."""
        return self.get_inputs()

    def view_outputs(self) -> List[HackathonOutput]:
        """Return the list of outputs (each with its score)."""
        return self.get_outputs()

    def view_score(self) -> HackathonScoring:
        """View the score object."""
        # Save scoring object if does not exist
        solution_key = self.get_key()
        scoring_key = HackathonScoringKey(solution=solution_key)
        if (result := Context.current().load_one(HackathonScoring, scoring_key, is_record_optional=True)) is None:
            result = HackathonScoring(solution=solution_key)
            Context.current().save_one(result)
        return result

    def get_trade_ids_list(self) -> List[int]:
        """Return the list of trade ids from the trade_ids string."""
        if not self.trade_ids:
            return []

        result = set()
        parts = self.trade_ids.split(",")

        for part in parts:
            part = part.strip()
            # Check if the part is a range like "1-3"
            if "-" in part:
                start, end = sorted([int(range_part) for range_part in part.split("-")])
                # Add the range of numbers to the result
                result.update(range(start, end + 1))
                continue

            # Add single number to the result
            result.add(int(part))

        return sorted(list(result))

    def get_inputs(self) -> List[HackathonInput]:
        """Return the list of inputs specified by the trade list."""
        inputs = Context.current().load_all(HackathonInput)

        # Filter inputs by trade_group and trade_ids
        return [
            x
            for x in inputs
            if x.trade_group == self.trade_group
            and not ((ids_list := self.get_trade_ids_list()) or x.trade_id in ids_list)
        ]

    def get_outputs(self) -> List[HackathonOutput]:
        """Return the list of outputs (each with its score)."""
        outputs = Context.current().load_all(HackathonOutput)

        return [x for x in outputs if x.solution.solution_id == self.solution_id]

    @abstractmethod
    def _process_input(self, input_: HackathonInput, *, trial_id: str) -> HackathonOutput:
        """Process one input and return one output."""

    def process_all_inputs(self, *, trial_id: str) -> None:
        # Process inputs
        for input_ in self.get_inputs():
            output_ = self._process_input(input_, trial_id=trial_id)
            output_.trial_id = trial_id
            Context.current().save_one(output_)

        Context.current().save_one(self)

    def run_generate(self) -> None:
        """Load, filter, and process HackathonInput data, then save results."""
        # Process all inputs assigning trial_id of 0
        self.process_all_inputs(trial_id="0")

    def run_score(self) -> None:
        """Create scoring object for solution."""
        HackathonScoring(solution=self.get_key()).run_score()
