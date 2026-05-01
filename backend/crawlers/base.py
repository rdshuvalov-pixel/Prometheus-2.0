from __future__ import annotations

from abc import ABC, abstractmethod

from backend.models.raw import RawVacancy


class CrawlerBase(ABC):
    name: str = "base"

    @abstractmethod
    async def fetch(self, url: str, company: str, tier: str) -> list[RawVacancy]:
        raise NotImplementedError
