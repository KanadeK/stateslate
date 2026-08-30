"""Built-in StateSlate demonstration project."""

from __future__ import annotations

import tempfile
from pathlib import Path

from stateslate.models import Project
from stateslate.parser import load_project

DEMO_JSON = """{
  "schema_version": 1,
  "title": "Moonlit Letter",
  "tracks": [
    {
      "id": "mara.coat",
      "label": "Mara's blue coat",
      "category": "wardrobe",
      "initial": "clean_buttoned"
    },
    {
      "id": "letter.seal",
      "label": "Red letter seal",
      "category": "props",
      "initial": "sealed"
    },
    {
      "id": "cafe.glass",
      "label": "Cafe water glass",
      "category": "props",
      "initial": "full"
    }
  ],
  "scenes": [
    {
      "id": "S10",
      "title": "The letter arrives",
      "story_order": 10,
      "shoot": {"day": 4, "order": 1},
      "tracks": ["mara.coat", "letter.seal"],
      "transitions": [
        {
          "track": "letter.seal",
          "from": "sealed",
          "to": "opened",
          "note": "Mara breaks the seal on camera"
        }
      ]
    },
    {
      "id": "S20",
      "title": "Rain in the alley",
      "story_order": 20,
      "shoot": {"day": 1, "order": 1},
      "tracks": ["mara.coat", "letter.seal"],
      "expects": {"letter.seal": "opened"},
      "transitions": [
        {
          "track": "mara.coat",
          "from": "clean_buttoned",
          "to": "rain_soaked_open",
          "note": "Coat becomes wet during the scene"
        }
      ]
    },
    {
      "id": "S30",
      "title": "The diner confession",
      "story_order": 30,
      "shoot": {"day": 1, "order": 2},
      "tracks": ["mara.coat", "cafe.glass"],
      "expects": {"mara.coat": "rain_soaked_open"},
      "transitions": [
        {
          "track": "cafe.glass",
          "from": "full",
          "to": "half",
          "note": "Mara drinks during the confession"
        }
      ]
    },
    {
      "id": "S40",
      "title": "Morning pickup",
      "story_order": 40,
      "shoot": {"day": 6, "order": 1},
      "tracks": ["mara.coat", "cafe.glass"],
      "expects": {
        "mara.coat": "rain_soaked_open",
        "cafe.glass": "half"
      },
      "transitions": []
    }
  ]
}
"""


def demo_project() -> Project:
    """Parse the embedded demo through the same public file boundary."""

    with tempfile.TemporaryDirectory(prefix="stateslate-demo-input-") as directory:
        path = Path(directory) / "moonlit-letter.json"
        path.write_text(DEMO_JSON, encoding="utf-8", newline="\n")
        return load_project(path)
