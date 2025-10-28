"""Confluence API client for fetching pages with label filtering."""

import re
from typing import List, Dict, Any, Generator
from html import unescape

import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config import Settings


class ConfluenceClient:
    """Client for interacting with Confluence REST API."""

    def __init__(self, settings: Settings):
        """
        Initialize Confluence client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = settings.confluence_url.rstrip("/")
        self.auth = (settings.confluence_username, settings.confluence_api_token)
        self.timeout = 30.0

        logger.info(f"Initialized Confluence client for {self.base_url}")

    def _clean_html(self, html_content: str) -> str:
        """
        Clean HTML content and extract plain text.

        Args:
            html_content: HTML content from Confluence

        Returns:
            Cleaned plain text
        """
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html_content)

        # Decode HTML entities
        text = unescape(text)

        # Remove multiple spaces and newlines
        text = re.sub(r"\s+", " ", text)

        # Trim
        text = text.strip()

        return text

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def _make_request(
        self, method: str, endpoint: str, params: Dict[str, Any] | None = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Confluence API with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.debug(f"Making {method} request to {url}")

            response = await client.request(
                method=method, url=url, auth=self.auth, params=params
            )

            response.raise_for_status()

            return response.json()

    async def fetch_pages_by_space(
        self, space_key: str, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Fetch pages from a specific Confluence space.

        Args:
            space_key: Confluence space key
            limit: Number of pages per request

        Returns:
            List of Confluence pages
        """
        logger.info(f"Fetching pages from space: {space_key}")

        all_pages = []
        start = 0

        while True:
            params = {"spaceKey": space_key, "start": start, "limit": limit, "expand": "body.storage,metadata.labels"}

            try:
                data = await self._make_request("GET", "/rest/api/content", params=params)

                pages = data.get("results", [])
                if not pages:
                    break

                all_pages.extend(pages)
                start += len(pages)

                logger.debug(f"Fetched {len(pages)} pages from {space_key} (total: {len(all_pages)})")

                # Check if there are more pages
                if len(pages) < limit:
                    break

            except httpx.HTTPError as e:
                logger.error(f"Error fetching pages from space {space_key}: {e}")
                break

        logger.info(f"Total pages fetched from {space_key}: {len(all_pages)}")
        return all_pages

    async def fetch_pages_by_label(
        self, label: str, limit: int = 25
    ) -> List[Dict[str, Any]]:
        """
        Fetch pages with a specific label.

        Args:
            label: Confluence label to filter by
            limit: Number of pages per request

        Returns:
            List of Confluence pages
        """
        logger.info(f"Fetching pages with label: {label}")

        all_pages = []
        start = 0

        while True:
            params = {"label": label, "start": start, "limit": limit, "expand": "body.storage,metadata.labels"}

            try:
                data = await self._make_request("GET", "/rest/api/content", params=params)

                pages = data.get("results", [])
                if not pages:
                    break

                all_pages.extend(pages)
                start += len(pages)

                logger.debug(f"Fetched {len(pages)} pages with label {label} (total: {len(all_pages)})")

                # Check if there are more pages
                if len(pages) < limit:
                    break

            except httpx.HTTPError as e:
                logger.error(f"Error fetching pages with label {label}: {e}")
                break

        logger.info(f"Total pages fetched with label {label}: {len(all_pages)}")
        return all_pages

    def filter_pages_by_labels(
        self, pages: List[Dict[str, Any]], labels: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter pages that have any of the specified labels.

        Args:
            pages: List of Confluence pages
            labels: List of labels to filter by

        Returns:
            Filtered list of pages
        """
        if not labels:
            return pages

        filtered_pages = []
        labels_lower = [label.lower() for label in labels]

        for page in pages:
            page_labels = page.get("metadata", {}).get("labels", {}).get("results", [])
            page_label_names = [label.get("name", "").lower() for label in page_labels]

            # Check if page has any of the required labels
            if any(label in page_label_names for label in labels_lower):
                filtered_pages.append(page)

        logger.info(f"Filtered {len(filtered_pages)}/{len(pages)} pages by labels: {labels}")
        return filtered_pages

    async def fetch_all_pages(self) -> List[Dict[str, Any]]:
        """
        Fetch all pages based on configured space keys and labels.

        Returns:
            List of all fetched and filtered pages
        """
        all_pages = []
        seen_page_ids = set()

        # Fetch by space keys
        for space_key in self.settings.confluence_spaces_list:
            pages = await self.fetch_pages_by_space(space_key)

            # Add unique pages
            for page in pages:
                page_id = page.get("id")
                if page_id and page_id not in seen_page_ids:
                    all_pages.append(page)
                    seen_page_ids.add(page_id)

        # Fetch by labels (if any)
        for label in self.settings.confluence_labels_list:
            pages = await self.fetch_pages_by_label(label)

            # Add unique pages
            for page in pages:
                page_id = page.get("id")
                if page_id and page_id not in seen_page_ids:
                    all_pages.append(page)
                    seen_page_ids.add(page_id)

        # Apply label filtering if labels are configured
        if self.settings.confluence_labels_list:
            all_pages = self.filter_pages_by_labels(
                all_pages, self.settings.confluence_labels_list
            )

        logger.info(f"Total unique pages fetched: {len(all_pages)}")
        return all_pages

    def extract_page_content(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract relevant content from a Confluence page.

        Args:
            page: Confluence page object

        Returns:
            Extracted page data
        """
        page_id = page.get("id", "")
        title = page.get("title", "Untitled")

        # Extract HTML body
        body_html = (
            page.get("body", {})
            .get("storage", {})
            .get("value", "")
        )

        # Clean HTML to plain text
        body_text = self._clean_html(body_html)

        # Extract metadata
        space = page.get("space", {})
        space_key = space.get("key", "")
        space_name = space.get("name", "")

        labels = page.get("metadata", {}).get("labels", {}).get("results", [])
        label_names = [label.get("name", "") for label in labels]

        # Get version info
        version = page.get("version", {})
        version_number = version.get("number", 1)
        last_updated = version.get("when", "")

        return {
            "id": page_id,
            "title": title,
            "content": body_text,
            "space_key": space_key,
            "space_name": space_name,
            "labels": label_names,
            "version": version_number,
            "last_updated": last_updated,
            "url": f"{self.base_url}/pages/viewpage.action?pageId={page_id}",
        }

    async def ingest_documents(self) -> List[Dict[str, Any]]:
        """
        Main ingestion method to fetch and process all Confluence pages.

        Returns:
            List of processed documents
        """
        logger.info("Starting Confluence document ingestion")

        # Fetch all pages
        pages = await self.fetch_all_pages()

        # Extract content from pages
        documents = []
        for page in pages:
            try:
                document = self.extract_page_content(page)
                documents.append(document)
            except Exception as e:
                logger.error(f"Error extracting content from page {page.get('id', 'unknown')}: {e}")
                continue

        logger.info(f"Successfully ingested {len(documents)} documents")
        return documents
