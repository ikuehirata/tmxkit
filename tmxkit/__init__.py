"""tmxkit

tmxkit is a lightweight foundation library for streaming processing of TMX
(Translation Memory eXchange) files.

This top-level package aggregates the subpackages (`tmxkit.io`, `tmxkit.tu`,
`tmxkit.pipeline`) and re-exports common exceptions for convenience.

If Pylance does not show type hints, reinstall in editable strict mode:

    pip install -e ../tmxkit/ --config-settings editable_mode=strict

Example:
    from tmxkit import TmxParseError

Note: Most functionality is implemented in the subpackages; the top-level
package only exposes common types and exceptions.
"""
from __future__ import annotations

from . import ops, tu
from .errors import InvalidTUError, StreamError, TmxkitError, TmxParseError

__all__ = [
    # 例外（誰でも使う）
    'TmxkitError', 'TmxParseError', 'InvalidTUError', 'StreamError',
    # 高レベルAPI（ユーザー向け）
    'ops',
    # TU操作ユーティリティ（ユーザー向け）
    'tu',
    # io / pipeline / core は意図的に非公開
    # → 必要な人は from tmxkit.io import ... で明示的にimportする
]
