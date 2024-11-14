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

import re
from dataclasses import dataclass
from typing import Type
from typing_extensions import Self
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.records.dataclasses_extensions import missing
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_key

_MAX_TITLE_LEN = 1000
"""Maximum length of the description."""

_DISALLOWED_TITLE_SUBSTRINGS = {  # TODO: Use names from a consolidated list
    ":": "Colon",
    "(": "Left parenthesis",
    ")": "Right parenthesis",
    "\n": "End of line",
    "\r": "Carriage return",
}
"""These substrings are not allowed in description."""

_MD5_HEX_RE = re.compile(r"^[0-9a-f]+$")
"""Regex for MD5 hex."""


@dataclass(slots=True, kw_only=True)
class EntryKey(KeyMixin):
    """Contains description, body and supporting data of user entry along with the entry processing result."""

    entry_id: str = missing()
    """Based on record type, description and MD5 hash of body and data if present."""

    def init(self) -> None:
        # Check entry_id inside a key but not inside a record where it will be set automatically
        if is_key(self):
            # Check that entry_id consists of three backslash-delimited tokens
            # if len(self.entry_id.split("\\")) != 3:
            if len(self.entry_id.split(":")) != 2:
                # raise UserError(f"The following EntryId does not consist of three backslash-delimited tokens:\n"
                raise UserError(f"The following EntryId does not consist of two colon-delimited tokens:\n"
                                f"{self.entry_id}\n")

    @classmethod
    def get_key_type(cls) -> Type:
        return EntryKey

    @classmethod
    def get_entry_key(
        cls,
        description: str,
        body: str | None = None,
        data: str | None = None,
    ) -> Self:
        """Create the unique identifier from parameters."""
        record_type = cls.__name__
        result = EntryKey(entry_id=cls.get_entry_id(record_type, description, body=body, data=data))
        return result

    @classmethod
    def get_entry_id(
        cls,
        record_type: str,
        description: str,
        body: str | None = None,
        data: str | None = None,
    ) -> str:
        """Create the unique identifier from parameters."""

        # Initial checks for the description
        if StringUtil.is_empty(description):
            raise UserError(f"Empty 'description' field in {record_type}.")
        if len(description) > _MAX_TITLE_LEN:
            raise UserError(
                f"The length {len(description)} of the 'description' field in {record_type} exceeds {_MAX_TITLE_LEN}, "
                f"use 'Entry.body' field for the excess text."
            )
        description_substrings = [name for sub, name in _DISALLOWED_TITLE_SUBSTRINGS.items() if sub in description]
        if description_substrings:
            description_substrings_str = "\n".join(description_substrings)
            raise UserError(
                f"Field 'description' contains the following disallowed substrings:\n{description_substrings_str}\n. "
                f"Field text:\n{description}"
            )

        # Combine ClassName with description
        type_and_description = f"{record_type}: {description}"

        if not StringUtil.is_empty(body) or not StringUtil.is_empty(data):
            # Append MD5 hash in hexadecimal format of the body and data if at least one is present
            md5_hash = StringUtil.md5_hex(f"{body}.{data}")
            entry_id = f"{type_and_description} (MD5: {md5_hash})"
        else:
            # Otherwise use type and description only
            entry_id = type_and_description
        return entry_id

