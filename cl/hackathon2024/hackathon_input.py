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
from cl.hackathon2024.hackathon_input_key import HackathonInputKey
from cl.runtime import RecordMixin
from cl.runtime.records.dataclasses_extensions import missing


@dataclass(slots=True, kw_only=True)
class HackathonInput(HackathonInputKey, RecordMixin[HackathonInputKey]):
    """Input text for a single hackathon trade."""

    entry_text: str = missing()
    """Trade entry text for the specified trade."""

    def get_key(self) -> HackathonInputKey:
        return HackathonInputKey(trade_id=self.trade_id)
