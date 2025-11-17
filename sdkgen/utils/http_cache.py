"""HTTP cache for remote OpenAPI specifications."""

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx
import yaml


class HTTPCache:
    """Simple HTTP cache for fetching and caching remote resources.

    Provides caching functionality for HTTP GET requests, particularly useful
    for caching remote OpenAPI specifications. Stores cached content as JSON
    files in a local directory, with automatic handling of JSON and YAML
    content types.

    Attributes:
        cache_dir: Path to the directory where cached files are stored.
    """

    def __init__(self, cache_dir: Path | None = None):
        """Initialize HTTP cache with a specified or default cache directory.

        Creates the cache directory if it doesn't exist.

        Args:
            cache_dir: Directory to store cached files. If None, defaults to
                ~/.sdkgen/cache. The directory will be created with parent
                directories if it doesn't exist.

        Example:
            >>> cache = HTTPCache()  # Uses default cache dir
            >>> cache = HTTPCache(Path("/tmp/my_cache"))  # Custom cache dir
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".sdkgen" / "cache"

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cache_path(self, url: str) -> Path:
        """Get the cache file path for a given URL.

        Generates a unique filename by hashing the URL using SHA-256,
        ensuring consistent cache paths for the same URL.

        Args:
            url: URL to get cache path for. Can be any valid HTTP(S) URL.

        Returns:
            Path object pointing to the cache file location. The file may or
            may not exist yet.

        Example:
            >>> cache = HTTPCache()
            >>> path = cache.get_cache_path("https://api.example.com/spec.json")
            >>> print(path.name)
            'a3f5b8c...123.json'  # SHA-256 hash of the URL
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        return self.cache_dir / f"{url_hash}.json"

    async def fetch(self, url: str, force: bool = False) -> dict[str, Any]:
        """Fetch content from URL with automatic caching.

        Retrieves content from the cache if available, otherwise fetches from
        the URL and caches the result. Automatically detects and parses JSON
        and YAML content types.

        Args:
            url: URL to fetch. Must be a valid HTTP(S) URL.
            force: If True, bypass cache and refetch from URL even if cached.
                Defaults to False.

        Returns:
            Parsed content as a dictionary. For JSON and YAML URLs, this is
            the parsed structure. The cached content is stored separately from
            metadata.

        Raises:
            httpx.HTTPStatusError: If the HTTP request fails with a bad status code.
            httpx.RequestError: If the request fails (network error, timeout, etc.).
            yaml.YAMLError: If YAML content cannot be parsed.
            json.JSONDecodeError: If JSON content cannot be parsed.

        Example:
            >>> cache = HTTPCache()
            >>> spec = await cache.fetch("https://api.example.com/openapi.json")
            >>> print(spec.keys())
            dict_keys(['openapi', 'info', 'paths'])
            >>> # Second fetch uses cache
            >>> spec2 = await cache.fetch("https://api.example.com/openapi.json")
            >>> # Force refetch
            >>> spec3 = await cache.fetch("https://api.example.com/openapi.json", force=True)
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
        """Clear all cached files from the cache directory.

        Removes all .json files from the cache directory, effectively
        invalidating the entire cache. Does not remove the cache directory
        itself.

        Example:
            >>> cache = HTTPCache()
            >>> await cache.fetch("https://api.example.com/spec.json")
            >>> cache.clear()  # Removes all cached files
        """
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def clear_url(self, url: str) -> None:
        """Clear cache for a specific URL.

        Removes the cached file for the given URL if it exists. Does nothing
        if the URL has not been cached.

        Args:
            url: URL to clear from cache. Must be the exact URL that was
                originally cached.

        Example:
            >>> cache = HTTPCache()
            >>> await cache.fetch("https://api.example.com/spec.json")
            >>> cache.clear_url("https://api.example.com/spec.json")
            >>> # Next fetch will retrieve from URL again
            >>> spec = await cache.fetch("https://api.example.com/spec.json")
        """
        cache_path = self.get_cache_path(url)
        if cache_path.exists():
            cache_path.unlink()
