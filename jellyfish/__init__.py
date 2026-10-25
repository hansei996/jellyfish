"""一个能活、能死、能复活、能被人重看一生的东西。"""
from .core import decide, default_world, digest, initial_state, revive, step  # noqa: F401
from .log import Life  # noqa: F401

__version__ = "0.1.0"
__all__ = ["Life", "step", "decide", "revive", "initial_state", "digest"]