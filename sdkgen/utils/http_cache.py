"""HTTP cache for remote OpenAPI specifications."""

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx
import yaml


class HTTPCache:
    """Simple HTTP cache for fetching and caching remote resources."""

    def __init__(self, cache_dir: Path | None = None):
        """
        Initialize HTTP cache.

        Args:
            cache_dir: Directory to store cached files (default: ~/.sdkgen/cache)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".sdkgen" / "cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, url: str) -> Path:
        """
        Get cache file path for a URL.

        Args:
            url: URL to cache

        Returns:
            Path to cache file
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    async def fetch(self, url: str, force: bool = False) -> dict[str, Any]:
        """
        Fetch content from URL with caching.

        Args:
            url: URL to fetch
            force: Force refetch even if cached

        Returns:
            Content as dictionary
        """
        cache_path = self.get_cache_path(url)

        # Check cache
        if not force and cache_path.exists():
            with cache_path.open() as f:
                cached = json.load(f)
                return cached["content"]

        # Fetch from URL
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            response.raise_for_status()

            # Determine content type
            content_type = response.headers.get("content-type", "")

            if "json" in content_type:
                content = response.json()
            elif "yaml" in content_type or url.endswith((".yaml", ".yml")):
                content = yaml.safe_load(response.text)
            else:
                content = response.json()

            # Cache the result
            with cache_path.open("w") as f:
                json.dump({"url": url, "content": content}, f, indent=2)

            return content

    def clear(self) -> None:
        """Clear all cached files."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def clear_url(self, url: str) -> None:
        """
        Clear cache for a specific URL.

        Args:
            url: URL to clear from cache
        """
        cache_path = self.get_cache_path(url)
        if cache_path.exists():
            cache_path.unlink()
