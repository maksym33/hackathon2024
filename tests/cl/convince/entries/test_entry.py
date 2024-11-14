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

import pytest
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.testing.regression_guard import RegressionGuard
from cl.convince.entries.entry import Entry
from cl.convince.entries.entry_key import EntryKey
from cl.convince.entries.entry_type_key import EntryTypeKey


def test_create_key():
    """Test EntryKey.create_key method."""

    guard = RegressionGuard()

    # Record type
    entry_type = "Stub"
    locale = "en-GB"

    # Check with type and description only
    guard.write(EntryKey.create_key(entry_type=entry_type, locale=locale, text="Sample Text"))

    # Check with body
    guard.write(EntryKey.create_key(entry_type=entry_type, locale=locale, text=" ".join(20 * ["Long Text"])))

    # Check with data
    guard.write(EntryKey.create_key(entry_type=entry_type, locale=locale, text="Multiline\nText"))

    # Check with both
    guard.write(EntryKey.create_key(entry_type=entry_type, locale=locale, text="Sample Text", data="Sample Data"))

    # Verify
    guard.verify_all()


def test_check_entry_id():
    """Test EntryKey.check_entry_id method."""

    EntryKey(entry_id="a\\b\\c").init()
    EntryKey(entry_id="a\\b\\c\\d").init()
    with pytest.raises(UserError):
        EntryKey(entry_id="a").init()
    with pytest.raises(UserError):
        EntryKey(entry_id="a\\b").init()
    with pytest.raises(UserError):
        EntryKey(entry_id="a\\b\\c\\d\\e").init()


if __name__ == "__main__":
    pytest.main([__file__])
