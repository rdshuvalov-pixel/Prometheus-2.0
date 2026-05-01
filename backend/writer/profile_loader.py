from __future__ import annotations

from backend.db.client import get_active_profile
from backend.models.profile import CandidateProfile


def load_profile_for_writing() -> CandidateProfile:
    return get_active_profile()
