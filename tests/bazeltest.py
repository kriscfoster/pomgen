"""
Copyright (c) 2018, salesforce.com, inc.
All rights reserved.
SPDX-License-Identifier: BSD-3-Clause
For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
"""

from crawl import bazel
from crawl import dependency
import os
import unittest
import tempfile


class BazelTest(unittest.TestCase):

    def test_parse_maven_install(self):
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(MVN_INSTALL_JSON_CONTENT)

        result = bazel.parse_maven_install("maven", path)

        self.assertEqual(1, len(result))
        dep, transitives, exclusions = result[0]
        self.assertEqual(dependency.new_dep_from_maven_art_str("ch.qos.logback:logback-classic:1.2.3", "maven"), dep)
        self.assertEqual(2, len(transitives))
        self.assertEqual(dependency.new_dep_from_maven_art_str("ch.qos.logback:logback-core:1.2.3", "maven"), transitives[0])
        self.assertEqual(dependency.new_dep_from_maven_art_str("org.slf4j:slf4j-api:jar:1.7.30", "maven"), transitives[1])
        self.assertEqual(2, len(exclusions))
        self.assertEqual("jakarta.el", exclusions[0].group_id)
        self.assertEqual("jakarta.el-api", exclusions[0].artifact_id)
        self.assertEqual("org.glassfish", exclusions[1].group_id)
        self.assertEqual("jakarta.el", exclusions[1].artifact_id)

    def test_conflict_resolution_is_honored(self):
        """
        Verifies that the pinned file's "conflict_resolution" attribute is
        handled.
        """
        fd, path = tempfile.mkstemp()
        with os.fdopen(fd, 'w') as f:
            f.write(MVN_INSTALL_JSON_CONTENT_CONFLICT_RESOLUTION)

        result = bazel.parse_maven_install("maven", path)

        self.assertEqual(2, len(result))
        dep, transitives, exclusions = result[0]
        self.assertEqual(dependency.new_dep_from_maven_art_str("ch.qos.logback:logback-classic:1.2.3", "maven"), dep)
        self.assertEqual(1, len(transitives))
        transitive_guava = transitives[0]
        # we expect to get the dep from conflict_resolution map
        self.assertEqual(dependency.new_dep_from_maven_art_str("com.google.guava:guava:31.0.1-jre", "maven"), transitive_guava)
        guava, transitives, exclusions = result[1]
        # we expect to get the dep from conflict_resolution map
        self.assertEqual(dependency.new_dep_from_maven_art_str("com.google.guava:guava:31.0.1-jre", "maven"), guava)
        self.assertEqual(transitive_guava, guava)

    def test_target_pattern_to_path(self):
        """
        Tests for bazel.target_pattern_to_path.
        """
        self.assertEqual("foo/blah", bazel.target_pattern_to_path("//foo/blah"))
        self.assertEqual("foo/blah", bazel.target_pattern_to_path("/foo/blah"))
        self.assertEqual("foo/blah", bazel.target_pattern_to_path("foo/blah:target_name"))
        self.assertEqual("foo/blah", bazel.target_pattern_to_path("foo/blah/..."))
        self.assertEqual("foo/blah", bazel.target_pattern_to_path("foo/blah"))

    def test_ensure_unique_deps(self):
        """
        Tests for bazel._ensure_unique_deps
        """
        self.assertEqual(["//a", "//b", "//c"],
                          bazel._ensure_unique_deps(["//a", "//b", "//c", "//a"]))


MVN_INSTALL_JSON_CONTENT = """
{
    "dependency_tree": {
        "__AUTOGENERATED_FILE_DO_NOT_MODIFY_THIS_FILE_MANUALLY": -163681522,
        "conflict_resolution": {},
        "dependencies": [
            {
                "coord": "ch.qos.logback:logback-classic:1.2.3",
                "dependencies": [
                    "ch.qos.logback:logback-core:1.2.3",
                    "org.slf4j:slf4j-api:jar:1.7.30"
                ],
                "directDependencies": [
                    "org.slf4j:slf4j-api:1.7.30"
                ],
                "exclusions": [
                    "jakarta.el:jakarta.el-api",
                    "org.glassfish:jakarta.el"
                ]
            },
            {
                "coord": "ch.qos.logback:logback-classic:jar:sources:1.2.3",
                "dependencies": [
                    "org.slf4j:slf4j-api:jar:sources:1.7.30",
                    "ch.qos.logback:logback-core:jar:sources:1.2.3"
                ],
                "directDependencies": [
                    "ch.qos.logback:logback-core:jar:sources:1.2.3",
                    "org.slf4j:slf4j-api:jar:sources:1.7.30"
                ],
                "exclusions": [
                ]

            }
        ],
        "version": "0.1.0"
    }
}
"""

MVN_INSTALL_JSON_CONTENT_CONFLICT_RESOLUTION = """
{
    "dependency_tree": {
        "__AUTOGENERATED_FILE_DO_NOT_MODIFY_THIS_FILE_MANUALLY": -163681522,
        "conflict_resolution": {
            "com.google.guava:guava:31.0.1-jre": "com.google.guava:guava:31.0.1-jre-SNAPSHOT"
        },
        "dependencies": [
            {
                "coord": "ch.qos.logback:logback-classic:1.2.3",
                "dependencies": [
                    "com.google.guava:guava:31.0.1-jre-SNAPSHOT"
                ],
                "directDependencies": [
                    "com.google.guava:guava:31.0.1-jre-SNAPSHOT"
                ]
            },
            {
                "coord": "com.google.guava:guava:31.0.1-jre-SNAPSHOT",
                "dependencies": [],
                "directDependencies": [],
                "exclusions": [
                    "*:*"
                ]
            }
        ],
        "version": "0.1.0"
    }
}
"""

if __name__ == '__main__':
    unittest.main()
