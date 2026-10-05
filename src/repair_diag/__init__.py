"""repair-agent — hand-rolled diagnostic agent for the Detroit Diesel Series 60.

Ported from ctrl-a-jr. Same loop, registry, guard, activity log, and eval
runner. The new piece is a deterministic fault tree that decides which
question to ask next based on the answers so far.

    python -m repair_diag
"""

__version__ = "0.1.0"