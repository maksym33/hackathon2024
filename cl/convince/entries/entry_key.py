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
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.records.dataclasses_extensions import missing
from cl.runtime.records.key_mixin import KeyMixin
from cl.runtime.records.protocols import is_key

_DISALLOWED_DELIMITERS = {
    "\\": "Backslash",
    ";": "Semicolon",
}
"""These delimiters are not allowed in the text."""

_WHITESPACE_RE = re.compile(r'\s+')
"""Regex for whitespace replacement."""

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
            token_count = len(self.entry_id.split("\\"))
            if token_count != 3 and token_count != 4:
                raise UserError(f"EntryId must have three or four backslash-delimited tokens.\n"
                                f"EntryId: {self.entry_id}\n")

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
        result = EntryKey(entry_id=cls.create_key(record_type, description, body=body, data=data))
        return result

    @classmethod
    def create_key(
        cls,
        *,
        entry_type: str,
        text: str,
        locale: str,
        data: str | None = None,
    ) -> str:
        """Create the unique identifier from parameters."""

        # Initial checks for the description
        if StringUtil.is_empty(text):
            raise UserError(f"Empty 'text' field in {cls.__name__}.")

        # Generate digest if multiline or more than 80 characters
        if "\n" in text or len(text) > 80:
            # Get the first 160 characters, replace all whitespace by a single space and then truncate to 80
            is_truncated = True
            digest = text[:160].strip()
            digest = _WHITESPACE_RE.sub(" ", digest).strip()
            digest = digest[:80].strip()
        else:
            is_truncated = False
            digest = text

        delimiters = [name for sub, name in _DISALLOWED_DELIMITERS.items() if sub in text]
        if delimiters:
            delimiters_str = "\n".join(delimiters)
            raise UserError(
                f"Entry text digest contains the following disallowed delimiters:\n{delimiters_str}\n. "
                f"Digest:\n{digest}"
            )

        # EntryId without MD5 hash using type\digest\locale format
        base_entry_id = f"{entry_type}\\{digest}\\{locale}"

        if is_truncated or not StringUtil.is_empty(data):
            # Append MD5 hash in hexadecimal format if the text is truncated or data is present
            md5_hash = StringUtil.md5_hex(f"{text}{data}")
            entry_id = f"{base_entry_id}\\{md5_hash}"
        else:
            # Otherwise return without the hash
            entry_id = base_entry_id
        return entry_id
