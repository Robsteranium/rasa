from pathlib import Path
import textwrap
from typing import Text

import pytest

from rasa.shared.core.domain import Domain
from rasa.shared.core.events import ActionExecuted, UserUttered
from rasa.shared.core.trackers import DialogueStateTracker
from rasa.shared.core.training_data.story_reader.markdown_story_reader import (
    MarkdownStoryReader,
)
from rasa.shared.core.training_data.story_reader.yaml_story_reader import (
    YAMLStoryReader,
)
from rasa.shared.core.training_data.story_writer.yaml_story_writer import (
    YAMLStoryWriter,
)
from rasa.shared.core.training_data.structures import STORY_START


@pytest.mark.parametrize(
    "input_md_file, input_yaml_file",
    [
        ["data/test_stories/stories.md", "data/test_yaml_stories/stories.yml"],
        [
            "data/test_stories/stories_defaultdomain.md",
            "data/test_yaml_stories/stories_defaultdomain.yml",
        ],
    ],
)
async def test_simple_story(
    tmpdir: Path, default_domain: Domain, input_md_file: Text, input_yaml_file: Text
):

    original_md_reader = MarkdownStoryReader(
        default_domain, None, False, input_md_file, unfold_or_utterances=False
    )
    original_md_story_steps = original_md_reader.read_from_file(input_md_file)

    assert not YAMLStoryWriter.stories_contain_loops(original_md_story_steps)

    original_yaml_reader = YAMLStoryReader(default_domain, None, False)
    original_yaml_story_steps = original_yaml_reader.read_from_file(input_yaml_file)

    target_story_filename = tmpdir / "test.yml"
    writer = YAMLStoryWriter()
    writer.dump(target_story_filename, original_md_story_steps)

    processed_yaml_reader = YAMLStoryReader(default_domain, None, False)
    processed_yaml_story_steps = processed_yaml_reader.read_from_file(
        target_story_filename
    )

    assert len(processed_yaml_story_steps) == len(original_yaml_story_steps)
    for processed_step, original_step in zip(
        processed_yaml_story_steps, original_yaml_story_steps
    ):
        assert len(processed_step.events) == len(original_step.events)


async def test_story_start_checkpoint_is_skipped(default_domain: Domain):
    input_md_file = "data/test_stories/stories.md"

    original_md_reader = MarkdownStoryReader(
        default_domain, None, False, input_md_file, unfold_or_utterances=False
    )
    original_md_story_steps = original_md_reader.read_from_file(input_md_file)

    yaml_text = YAMLStoryWriter().dumps(original_md_story_steps)

    assert STORY_START not in yaml_text


async def test_forms_are_converted(default_domain: Domain):
    original_md_reader = MarkdownStoryReader(
        default_domain, None, False, unfold_or_utterances=False
    )
    original_md_story_steps = original_md_reader.read_from_file(
        "data/test_stories/stories_form.md"
    )

    assert YAMLStoryWriter.stories_contain_loops(original_md_story_steps)

    writer = YAMLStoryWriter()

    with pytest.warns(None) as record:
        writer.dumps(original_md_story_steps)

    assert len(record) == 0


def test_yaml_writer_dumps_user_messages():
    events = [UserUttered("Hello", {"name": "greet"}), ActionExecuted("utter_greet")]
    tracker = DialogueStateTracker.from_events("default", events)
    dump = YAMLStoryWriter().dumps(tracker.as_story().story_steps)

    assert (
        dump.strip()
        == textwrap.dedent(
            """
        version: "2.0"
        stories:
        - story: default
          steps:
          - intent: greet
            user: |-
              Hello
          - action: utter_greet

    """
        ).strip()
    )


def test_yaml_writer_avoids_dumping_not_existing_user_messages():
    events = [UserUttered("greet", {"name": "greet"}), ActionExecuted("utter_greet")]
    tracker = DialogueStateTracker.from_events("default", events)
    dump = YAMLStoryWriter().dumps(tracker.as_story().story_steps)

    assert (
        dump.strip()
        == textwrap.dedent(
            """
        version: "2.0"
        stories:
        - story: default
          steps:
          - intent: greet
          - action: utter_greet

    """
        ).strip()
    )


@pytest.mark.parametrize(
    "input_yaml_file", ["data/test_yaml_stories/rules_with_stories_sorted.yaml",],
)
def test_yaml_writer_dumps_rules(
    input_yaml_file: Text, tmpdir: Path, default_domain: Domain,
):
    original_yaml_reader = YAMLStoryReader(default_domain, None, False)
    original_yaml_story_steps = original_yaml_reader.read_from_file(input_yaml_file)

    dump = YAMLStoryWriter().dumps(original_yaml_story_steps)
    # remove the version string
    dump = "\n".join(dump.split("\n")[1:])

    with open(input_yaml_file) as original_file:
        assert dump == original_file.read()
