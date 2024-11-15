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

from cl.hackathon.hackathon_output import HackathonOutput
from cl.hackathon.hackathon_output_key import HackathonOutputKey
from cl.hackathon.hackathon_score_item import HackathonScoreItem
from cl.hackathon.hackathon_scoring_key import HackathonScoringKey
from cl.hackathon.hackathon_solution_key import HackathonSolutionKey
from cl.runtime import RecordMixin, Context
from cl.runtime.records.dataclasses_extensions import missing, field


@dataclass(slots=True, kw_only=True)
class HackathonScoring(HackathonScoringKey, RecordMixin[HackathonScoringKey]):
    """Class to perform scoring for hackathon solution."""

    score: int = missing()
    """Total score for hackathon solution."""

    maximum_score: int = missing()
    """Maximum possible score for solution."""

    details: List[HackathonScoreItem] = missing()
    """Detailed scoring info for each input."""

    trial_count: int = field(default=10)
    """Number of trials for each input."""

    def get_key(self):
        return HackathonScoringKey(solution=self.solution)

    @classmethod
    def get_score_item(cls, actual_output: HackathonOutput, expected_output: HackathonOutput) -> HackathonScoreItem:
        """Compare actual output with expected output and return HackathonScoreItem."""

        # Use expected output __slots__ as field names for comparison, excluding key slots
        expected_output_key_fields = expected_output.get_key().__slots__
        expected_output_fields = expected_output.__slots__

        matched_fields = []
        mismatched_fields = []

        # Iterate over expected output fields and compare values
        for field_name in [f for f in expected_output_fields if f not in expected_output_key_fields]:

            expected_field_value = getattr(expected_output, field_name, None)
            actual_field_value = getattr(actual_output, field_name, None)

            # TODO (Roman): Use custom comparison rules
            # Check equality for all fields
            if expected_field_value == actual_field_value:
                matched_fields.append(field_name)
            else:
                mismatched_fields.append(field_name)

        # Create and return score item
        return HackathonScoreItem(
            actual_output=actual_output.get_key(),
            expected_output=expected_output.get_key(),
            matched_fields=matched_fields,
            mismatched_fields=mismatched_fields
        )


    def calculate(self):
        """Calculate scoring info and record to self."""

        context = Context.current()

        # Load solution record
        solution = context.load_one(HackathonSolutionKey, self.solution)

        # Get solution inputs
        inputs = solution.get_inputs()

        # Set initial values of scoring fields
        details = []
        score = 0
        maximum_score = 0

        # Iterate over inputs, calculate scores and sum them up
        # It is assumed that all outputs exist
        for input_ in inputs:

            # Create expected output key for current input
            expected_output_key = HackathonOutputKey(
                solution=HackathonSolutionKey(solution_id="ExpectedResults"),
                trade_group=solution.trade_group,
                trade_id=input_.trade_id,
            )
            expected_output = context.load_one(HackathonOutput, expected_output_key)

            # Remember input key to create score items
            input_key = input_.get_key()

            # Load outputs for current input with trial_id
            for trial_index in range(1, self.trial_count+1):

                # Create actual output for current input and trial_index
                actual_output_key = HackathonOutputKey(
                    solution=self.solution,
                    trade_group=solution.trade_group,
                    trade_id=input_.trade_id,
                    trial_id=trial_index,
                )
                actual_output = context.load_one(HackathonOutput, actual_output_key)
                actual_output.scoring_trial_id = trial_index

                # Create a scoring item by comparing actual and expected outputs
                score_item = self.get_score_item(actual_output, expected_output)
                score_item.input = input_key

                # Sum up scores
                score += len(score_item.matched_fields)
                maximum_score += len(score_item.matched_fields) + len(score_item.mismatched_fields)

                details.append(score_item)

        # Update self with calculated values
        self.score = score
        self.maximum_score = score
        self.details = details