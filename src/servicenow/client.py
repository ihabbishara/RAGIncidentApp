"""ServiceNow API client for incident management."""

from typing import Dict, Any, Optional

import httpx
from loguru import logger
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from src.config import Settings


class ServiceNowClient:
    """Client for ServiceNow Table API operations."""

    def __init__(self, settings: Settings):
        """
        Initialize ServiceNow client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.base_url = settings.servicenow_url.rstrip("/")
        self.auth = (settings.servicenow_username, settings.servicenow_password)
        self.api_version = settings.servicenow_api_version
        self.timeout = 30.0

        logger.info(f"Initialized ServiceNow client for {self.base_url}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make HTTP request to ServiceNow API with retry logic.

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request payload
            params: Query parameters

        Returns:
            Response JSON

        Raises:
            httpx.HTTPError: If request fails after retries
        """
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.debug(f"Making {method} request to {url}")

            response = await client.request(
                method=method,
                url=url,
                auth=self.auth,
                headers=headers,
                json=data,
                params=params,
            )

            response.raise_for_status()

            return response.json()

    async def create_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new incident in ServiceNow.

        Args:
            incident_data: Incident details

        Returns:
            Created incident record

        Raises:
            httpx.HTTPError: If incident creation fails
        """
        logger.info(f"Creating ServiceNow incident: {incident_data.get('short_description', 'N/A')}")

        try:
            result = await self._make_request(
                method="POST",
                endpoint="/api/now/table/incident",
                data=incident_data,
            )

            incident = result.get("result", {})
            incident_number = incident.get("number", "Unknown")
            sys_id = incident.get("sys_id", "Unknown")

            logger.info(
                f"Successfully created incident {incident_number} (sys_id: {sys_id})"
            )

            return incident

        except Exception as e:
            logger.error(f"Failed to create ServiceNow incident: {e}")
            raise

    async def get_incident(self, sys_id: str) -> Dict[str, Any]:
        """
        Get incident by sys_id.

        Args:
            sys_id: ServiceNow sys_id

        Returns:
            Incident record
        """
        logger.debug(f"Fetching incident: {sys_id}")

        try:
            result = await self._make_request(
                method="GET",
                endpoint=f"/api/now/table/incident/{sys_id}",
            )

            return result.get("result", {})

        except Exception as e:
            logger.error(f"Failed to fetch incident {sys_id}: {e}")
            raise

    async def update_incident(
        self, sys_id: str, update_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing incident.

        Args:
            sys_id: ServiceNow sys_id
            update_data: Fields to update

        Returns:
            Updated incident record
        """
        logger.info(f"Updating incident: {sys_id}")

        try:
            result = await self._make_request(
                method="PATCH",
                endpoint=f"/api/now/table/incident/{sys_id}",
                data=update_data,
            )

            return result.get("result", {})

        except Exception as e:
            logger.error(f"Failed to update incident {sys_id}: {e}")
            raise

    async def search_incidents(
        self, query: str, limit: int = 100
    ) -> list[Dict[str, Any]]:
        """
        Search incidents using query.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching incidents
        """
        logger.debug(f"Searching incidents with query: {query}")

        try:
            result = await self._make_request(
                method="GET",
                endpoint="/api/now/table/incident",
                params={
                    "sysparm_query": query,
                    "sysparm_limit": limit,
                },
            )

            incidents = result.get("result", [])
            logger.info(f"Found {len(incidents)} incidents matching query")

            return incidents

        except Exception as e:
            logger.error(f"Failed to search incidents: {e}")
            raise

    async def check_health(self) -> bool:
        """
        Check if ServiceNow API is accessible.

        Returns:
            True if healthy, False otherwise
        """
        try:
            # Try to get a single incident (just to check connectivity)
            await self._make_request(
                method="GET",
                endpoint="/api/now/table/incident",
                params={"sysparm_limit": 1},
            )

            logger.info("ServiceNow API is healthy")
            return True

        except Exception as e:
            logger.error(f"ServiceNow health check failed: {e}")
            return False
