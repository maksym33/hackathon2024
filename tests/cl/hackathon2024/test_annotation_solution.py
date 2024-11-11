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

from cl.hackathon2024.annotation_solution import AnnotationSolution
from cl.runtime.context.testing_context import TestingContext
from cl.runtime.settings.preload_settings import PreloadSettings


def test_annotation_solution():
    """Test AnnotationSolution preload."""

    with TestingContext() as context:

        # Save records from preload directory to DB and execute run_configure on all preloaded Config records
        PreloadSettings.instance().save_and_configure()

        # Load AnnotationSolution records
        solutions = context.load_all(AnnotationSolution)
        for solution in solutions:
            pass  # TODO: Perform scoring and record the output



