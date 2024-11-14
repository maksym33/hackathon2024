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
import re
from abc import abstractmethod
from dataclasses import dataclass
from typing import Type

from cl.convince.settings.convince_settings import ConvinceSettings
from cl.runtime import Context
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.primitive.case_util import CaseUtil
from cl.runtime.primitive.string_util import StringUtil
from cl.runtime.records.dataclasses_extensions import missing
from cl.runtime.records.record_mixin import RecordMixin
from cl.convince.entries.entry_key import EntryKey

_DISALLOWED_DELIMITERS = {
    "\\": "Backslash",
    ";": "Semicolon",
}
"""These delimiters are not allowed in the text."""

_WHITESPACE_RE = re.compile(r'\s+')
"""Regex for whitespace replacement."""


@dataclass(slots=True, kw_only=True)
class Entry(EntryKey, RecordMixin[EntryKey], ABC):
    """Contains description, body and supporting data of user entry along with the entry processing result."""

    entry_type: str = missing()
    """Entry type string is set in 'init' method of a descendant of this class."""

    text: str = missing()
    """Description exactly as provided by the user (included in MD5 hash)."""

    locale: str = missing()
    """Locale in BCP 47 ll-CC where ll is language and CC is country (included in MD5 hash)."""

    data: str | None = None
    """Optional supporting data in YAML format (included in MD5 hash)."""

    verified: bool | None = None
    """Flag indicating the entry is verified."""

    def get_key(self) -> EntryKey:
        return EntryKey(entry_id=self.entry_id)

    def init(self) -> None:
        """Generate entry_id in 'type: description' format followed by an MD5 hash of body and data if present."""

        # Check text
        if StringUtil.is_empty(self.text):
            raise UserError(f"Empty 'text' field in {type(self).__name__}.")

        # Check locale format or set based on the default in ConvinceSettings if not specified
        if self.locale is not None:
            # This performs validation
            ConvinceSettings.parse_locale(self.locale)
        else:
            self.locale = ConvinceSettings.instance().locale

        # Convert field types if necessary
        if self.verified is not None and isinstance(self.verified, str):
            self.verified = self.parse_optional_bool(self.verified, field_name="verified")

        # Base type resolves the ambiguity of different entry types with the same text
        base_type = self.get_base_type()
        self.entry_type = base_type.__name__.removesuffix("Entry")

        # Generate digest if multiline or more than 80 characters
        if "\n" in self.text or len(self.text) > 80:
            # Get the first 160 characters, replace all whitespace by a single space and then truncate to 80
            is_truncated = True
            digest = self.text[:160].strip()
            digest = _WHITESPACE_RE.sub(" ", digest).strip()
            digest = digest[:80].strip()
        else:
            is_truncated = False
            digest = self.text

        delimiters = [name for sub, name in _DISALLOWED_DELIMITERS.items() if sub in digest]
        if delimiters:
            delimiters_str = "\n".join(delimiters)
            raise UserError(
                f"Entry text digest contains the following disallowed delimiters:\n{delimiters_str}\n. "
                f"Digest:\n{digest}"
            )

        if is_truncated or not StringUtil.is_empty(self.data):
            # Append MD5 hash in hexadecimal format if the text is truncated or data is present
            md5_hash = StringUtil.md5_hex(f"{self.text}{self.data}")
            self.entry_id = f"{digest} ({self.entry_type}, {self.locale}, {md5_hash})"
        else:
            # Otherwise return without the hash
            self.entry_id = f"{digest} ({self.entry_type}, {self.locale})"

    @abstractmethod
    def get_base_type(self) -> Type:
        """Lowest level of class hierarchy that resolves the ambiguity of different entry types with the same text."""

    def get_text(self) -> str:
        """Get the complete text of the entry."""
        # TODO: Support data
        if self.data is not None:
            raise RuntimeError("Entry 'data' field is not yet supported.")
        result = self.text
        return result

    # TODO: Restore abstract when implemented for all entries
    def run_generate(self) -> None:
        """Generate or regenerate the proposed value."""
        raise UserError(f"Propose handler is not yet implemented for {type(self).__name__}.")

    def run_reset(self) -> None:
        """Clear all output  fields and verification flag."""
        if self.verified:
            raise UserError(
                f"Entry {self.entry_id} is marked as verified, run Unmark Verified before running Reset."
                f"This is a safety feature to prevent overwriting verified entries. "
            )
        record_type = type(self)
        result = record_type(
            description=self.text,
            data=self.data,
            lang=self.lang,
        )
        Context.current().save_one(result)

    def run_mark_verified(self) -> None:
        """Mark verified."""
        self.verified = True
        Context.current().save_one(self)

    def run_unmark_verified(self) -> None:
        """Unmark verified."""
        self.verified = False
        Context.current().save_one(self)

    @classmethod
    def parse_required_bool(
        cls, field_value: str | None, *, field_name: str | None = None
    ) -> bool:  # TODO: Move to Util class
        """Parse an optional boolean value."""
        match field_value:
            case None | "":
                field_name = CaseUtil.snake_to_pascal_case(field_name)
                for_field = f"for field {field_name}" if field_name is not None else " for a Y/N field"
                raise UserError(f"The value {for_field} is empty. Valid values are Y or N.")
            case "Y":
                return True
            case "N":
                return False
            case _:
                field_name = CaseUtil.snake_to_pascal_case(field_name)
                for_field = f" for field {field_name}" if field_name is not None else " for a Y/N field"
                raise UserError(f"The value {for_field} must be Y, N or an empty string.\nField value: {field_value}")

    @classmethod
    def parse_optional_bool(
        cls, field_value: str | None, *, field_name: str | None = None
    ) -> bool | None:  # TODO: Move to Util class
        """Parse an optional boolean value."""
        match field_value:
            case None | "":
                return None
            case "Y":
                return True
            case "N":
                return False
            case _:
                field_name = CaseUtil.snake_to_pascal_case(field_name)
                for_field = f" for field {field_name}" if field_name is not None else ""
                raise UserError(f"The value{for_field} must be Y, N or an empty string.\nField value: {field_value}")
