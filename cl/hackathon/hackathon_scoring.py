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
from typing import Final, List
from typing_extensions import Self

from cl.hackathon.hackathon_input import HackathonInput
from cl.hackathon.hackathon_scoring_statistics import HackathonScoringStatistics
from cl.runtime import Context
from cl.runtime import RecordMixin
from cl.runtime.plots.heat_map_plot import HeatMapPlot
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.records.dataclasses_extensions import field
from cl.runtime.records.dataclasses_extensions import missing
from cl.hackathon.hackathon_input_key import HackathonInputKey
from cl.hackathon.hackathon_output import HackathonOutput
from cl.hackathon.hackathon_output_key import HackathonOutputKey
from cl.hackathon.hackathon_score_item import HackathonScoreItem
from cl.hackathon.hackathon_scoring_key import HackathonScoringKey
from cl.hackathon.hackathon_solution_key import HackathonSolutionKey


@dataclass(slots=True, kw_only=True)
class HackathonScoring(HackathonScoringKey, RecordMixin[HackathonScoringKey]):
    """Class to perform scoring for hackathon solution."""

    trial_count: int | None = None
    """Number of trials for each input."""

    score: int | None = None
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

    def run_score(self) -> None:
        """Create scoring object for solution."""

        # Reset to prevent the old score from being visible duirng the scoring run
        self.run_reset()

        # TODO (Roman): Consider updating outputs for scoring elsewhere
        self.update_outputs()

        # Compare solution outputs with expected outputs and save HackathonScoreItems for each pair
        self.calculate()

        # Save scoring object with total score
        Context.current().save_one(self)

    def run_reset(self) -> None:
        """Reset the score."""
        self.score = None
        self.max_score = None
        Context.current().save_one(self)

    def get_score_item(
        self, input_key: HackathonInputKey, actual_output: HackathonOutput, expected_output: HackathonOutput
    ) -> HackathonScoreItem:
        """Compare actual output with expected output and return HackathonScoreItem."""

        # Use expected output __slots__ as field names for comparison, excluding key slots
        expected_output_key_fields = expected_output.get_key().__slots__
        expected_output_fields = expected_output.__slots__

        matched_fields = []
        mismatched_fields = []

        # Iterate over expected output fields and compare values
        for field_name in [f for f in expected_output_fields if f not in expected_output_key_fields]:
            # TODO (Roman): Use custom comparison rules

            # Skip entry_text field
            if field_name == "entry_text":
                continue

            expected_field_value = getattr(expected_output, field_name, None)
            actual_field_value = getattr(actual_output, field_name, None)

            # Check equality for all fields
            if expected_field_value == actual_field_value:
                matched_fields.append(field_name)
            else:
                mismatched_fields.append(field_name)

        # Create and return score item
        return HackathonScoreItem(
            scoring=self.get_key(),
            input=input_key,
            actual_output=actual_output.get_key(),
            expected_output=expected_output.get_key(),
            matched_fields=matched_fields,
            mismatched_fields=mismatched_fields,
        )

    def update_outputs(self):

        # Load solution record
        solution = Context.current().load_one(HackathonSolutionKey, self.solution)

        # Run processing trial_count times
        for trial_index in range(1, self.trial_count + 1):
            solution.process_all_inputs(trial_id=str(trial_index))

    def calculate(self):
        """Calculate scoring info and record to self."""

        context = Context.current()

        # Get solution inputs
        inputs = self._get_inputs()

        # Set initial values of scoring fields
        details = []
        score = 0
        max_score = 0

        # Iterate over inputs, calculate scores and sum them up
        # It is assumed that all outputs exist
        for input_ in inputs:

            # Get expected output key for current input
            expected_output = input_.get_expected_output()

            # Remember input key to create score items
            input_key = input_.get_key()

            # Load outputs for current input with trial_id
            for trial_index in range(1, self.trial_count + 1):
                trial_id = str(trial_index)

                # Create actual output for current input and trial_index
                actual_output_key = HackathonOutputKey(
                    solution=self.solution,
                    trade_group=input_.trade_group,
                    trade_id=input_.trade_id,
                    trial_id=trial_id,
                )
                actual_output = context.load_one(HackathonOutput, actual_output_key)

                # Create a scoring item by comparing actual and expected outputs
                score_item = self.get_score_item(input_key, actual_output, expected_output)
                Context.current().save_one(score_item)

                # Sum up scores
                score += len(score_item.matched_fields)
                max_score += len(score_item.matched_fields) + len(score_item.mismatched_fields)

                details.append(score_item.get_key())

        # Update self with calculated values
        self.score = score
        self.max_score = max_score

    def _get_inputs(self) -> List[HackathonInput]:
        """Return the list of inputs specified by solution."""
        solution = Context.current().load_one(HackathonSolutionKey, self.solution)
        return solution.get_inputs()

    def view_heatmap(self) -> None:
        """Heatmap with average scores for each field and trade."""

        context = Context.current()

        scoring_items = context.load_all(HackathonScoreItem)
        filtered_scoring_items = [item for item in scoring_items if item.scoring == self.get_key()]

        if len(filtered_scoring_items) == 0:
            return None

        first_item = filtered_scoring_items[0]
        fields = first_item.matched_fields + first_item.mismatched_fields

        # Get solution inputs
        inputs = self._get_inputs()

        result_values = []

        # Group scoring items by their input key for faster lookup
        scoring_items_by_input = defaultdict(list)
        for item in filtered_scoring_items:
            scoring_items_by_input[item.input.trade_id].append(item)

        # Main loop to process each hackathon input
        for input_ in inputs:
            # Initialize the score dictionary with all fields set to 0
            score_dict = {field_name: 0 for field_name in fields}
            hackathon_input_key = input_.get_key()

            # Get all scoring items for the current input key
            scoring_items_for_input = scoring_items_by_input.get(hackathon_input_key.trade_id, [])

            # Update scores for matched fields
            for item in scoring_items_for_input:
                for matched_field in item.matched_fields:
                    score_dict[matched_field] += 1

            # Append all field scores to the result list
            result_values.extend(score_dict.values())

        # Normalize the results
        normalized_result_values = [round(result / self.trial_count, 2) for result in result_values]

        maximum_values = [1] * len(fields) * len(inputs)

        num_trades = len(inputs)
        num_fields = len(fields)

        row_labels = []

        for i in range(num_trades):
            row_labels += [f"Trade {i + 1}"] * num_fields

        fields_labels = [CaseUtil.snake_to_title_case(file_name).replace("Leg ", "") for file_name in fields]
        col_labels = fields_labels * num_trades

        heat_map_plot = HeatMapPlot(plot_id="heat_map_plot")
        heat_map_plot.row_labels = row_labels
        heat_map_plot.col_labels = col_labels
        heat_map_plot.received_values = normalized_result_values
        heat_map_plot.expected_values = maximum_values
        heat_map_plot.x_label = "Fields"
        heat_map_plot.y_label = "Trades"

        return heat_map_plot.get_view()

    def view_statistics(self) -> List[HackathonScoringStatistics]:
        """Generate scoring statistics for a hackathon solution."""

        context = Context.current()

        # Get solution inputs
        inputs = self._get_inputs()

        # Load all hackathon outputs
        all_outputs = context.load_all(HackathonOutput)

        # Identify fields to compare, excluding key fields and 'entry_text'
        first_output = all_outputs[0]
        expected_output_key_fields = first_output.get_key().__slots__
        expected_output_fields = first_output.__slots__
        fields_to_compare = [f for f in expected_output_fields if
                             f not in expected_output_key_fields and f != "entry_text"]

        all_statistics = []
        for input_ in inputs:
            # Initialize statistics object for each input
            statistics = HackathonScoringStatistics(
                solution=self.solution,
                trade_id=input_.trade_id,
                entry_text=input_.entry_text
            )

            # Filter outputs corresponding to the current input
            filtered_outputs = [output for output in all_outputs
                                if output.solution == self.solution and output.trade_group == input_.trade_group
                                and output.trade_id == input_.trade_id]

            # Get expected output key for current input
            expected_output = input_.get_expected_output()

            for field_name in fields_to_compare:
                # Gather values for the current field
                actual_field_values = [getattr(output, field_name, None) for output in filtered_outputs]
                actual_field_values = ["Error" if val and val.startswith("Error") else val
                                       for val in actual_field_values]

                expected_field_value = getattr(expected_output, field_name, None)

                # Generate statistics summary for the field
                field_statistics = f"{expected_field_value} (exp)\n" + "\n".join(map(
                    lambda x: f"{x[0]} ({x[1]}/{self.trial_count})" if x[1] > 1 else x[0],
                    Counter(actual_field_values).items()
                ))

                # Assign the statistics to the corresponding field in the statistics object
                setattr(statistics, field_name, field_statistics)

            # Save and collect the statistics object
            context.save_one(statistics)
            all_statistics.append(statistics)

        return all_statistics

