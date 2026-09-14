"""Fail Python package builds with stale UI; consumers do not need Node."""
from pathlib import Path
import runpy
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class UiBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        root = Path(self.root)
        runpy.run_path(str(root / 'tools/check_ui.py'))['check'](root)
