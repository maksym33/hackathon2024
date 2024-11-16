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

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing_extensions import Self
from cl.runtime.experiments.trial_key import TrialKey
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.records.dataclasses_extensions import missing
from cl.runtime.records.record_mixin import RecordMixin
from cl.convince.llms.completion_key import CompletionKey
from cl.convince.llms.llm_key import LlmKey


@dataclass(slots=True, kw_only=True)
class Completion(CompletionKey, RecordMixin[CompletionKey], ABC):
    """Provides an API for single query and chat completion."""

    llm: LlmKey = missing()
    """LLM for which the completion is recorded."""

    trial: TrialKey | None = None
    """Trial for which the completion is recorded."""

    timestamp: str = missing()
    """
    Globally unique UUIDv7 (RFC-9562) timestamp in time-ordered dash-delimited string format with additional
    strict time ordering guarantees within the same process, thread and context.
    """

    query: str = missing()
    """Query for which the completion is recorded."""

    completion: str = missing()
    """Completion returned by the LLM."""

    def get_key(self) -> CompletionKey:
        return CompletionKey(completion_id=self.completion_id)

    def init(self) -> Self:
        """Generate entry_id from llm_id, trial_id and query fields."""

        # Check that required fields are set
        if self.llm is None:
            raise UserError(f"Empty 'llm' field in {type(self).__name__}.")
        if StringUtil.is_empty(self.query):
            raise UserError(f"Empty 'query' field in {type(self).__name__}.")

        # Create a unique time-ordered identifier
        self.timestamp = Timestamp.create()

        # Generate digest if multiline or more than 80 characters
        self.completion_id = StringUtil.digest(
            self.query,
            text_params=(
                self.llm.llm_id,
                self.trial.trial_id,
            ),
        )

        # Return self to enable method chaining
        return self
