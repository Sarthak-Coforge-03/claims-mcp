"""Test doubles: repository base classes implemented in memory, used only by tests.

They subclass the real *_repository_base classes, so a fake missing a required method can't even
be created. Importable from tests as `fakes.*` because pyproject sets pytest's pythonpath to tests/.
"""
