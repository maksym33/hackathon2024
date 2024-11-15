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

from dataclasses import dataclass, field
from typing import List
from cl.hackathon.hackathon_score_item_key import HackathonScoreItemKey
from cl.runtime import RecordMixin


@dataclass(slots=True, kw_only=True)
class HackathonScoreItem(HackathonScoreItemKey, RecordMixin[HackathonScoreItemKey]):
    """Base scoring info for specified actual and expected outputs."""

    matched_fields: List[str] = field(default_factory=list)
    """List of matched fields."""

    mismatched_fields: List[str] = field(default_factory=list)
    """List of mismatched fields."""

    def get_key(self):
        return HackathonScoreItemKey(
            scoring=self.scoring,
            input=self.input,
            actual_output=self.actual_output,
            expected_output=self.expected_output
        )
