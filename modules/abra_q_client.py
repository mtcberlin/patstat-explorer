"""
Abra-Q API Client for Query Generation
Handles authentication, token management, and query generation via Abra-Q service.
"""
import os
import requests
import json
from typing import Optional, Dict
from datetime import datetime, timedelta


class AbraQClient:
    """Client for interacting with Abra-Q query generation service."""

    def __init__(
        self,
        api_url: Optional[str] = None,
        email: Optional[str] = None,
        password: Optional[str] = None,
        datasource: Optional[str] = None
    ):
        """Initialize Abra-Q client with credentials.

        Args:
            api_url: Base URL for Abra-Q API (default from env)
            email: Login email (default from env)
            password: Login password (default from env)
            datasource: Datasource name (default from env)
        """
        self.api_url = api_url or os.getenv("ABRAQ_API_URL", "https://5i3vp2k9zz.eu-central-1.awsapprunner.com")
        self.email = email or os.getenv("ABRAQ_EMAIL")
        self.password = password or os.getenv("ABRAQ_PASSWORD")
        self.datasource = datasource or os.getenv("ABRAQ_DATASOURCE", "arne-patstat")

        self._token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None

    def _is_token_valid(self) -> bool:
        """Check if current token is still valid."""
        if not self._token:
            return False
        if not self._token_expiry:
            return False
        # Consider token invalid 5 minutes before actual expiry
        return datetime.now() < (self._token_expiry - timedelta(minutes=5))

    def _authenticate(self) -> bool:
        """Authenticate with Abra-Q and obtain access token.

        Returns:
            True if authentication successful, False otherwise
        """
        if not self.email or not self.password:
            raise ValueError("Abra-Q credentials not configured. Set ABRAQ_EMAIL and ABRAQ_PASSWORD.")

        try:
            url = f"{self.api_url}/users/login"
            payload = {
                "email": self.email,
                "password": self.password
            }
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            # Extract token from response
            data = response.json()
            self._token = data.get('token') or data.get('abra-q-token')

            if not self._token:
                # Try to get from cookies
                self._token = response.cookies.get('abra-q-token')

            if self._token:
                # Set token expiry (assume 24 hours if not provided)
                self._token_expiry = datetime.now() + timedelta(hours=24)
                return True
            else:
                raise ValueError("No token received from authentication response")

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to authenticate with Abra-Q: {str(e)}")

    def _get_token(self) -> str:
        """Get valid authentication token, refreshing if necessary.

        Returns:
            Valid authentication token

        Raises:
            ConnectionError: If authentication fails
        """
        if not self._is_token_valid():
            self._authenticate()
        return self._token

    def generate_query(self, question: str) -> Dict:
        """Generate SQL query from natural language question.

        Args:
            question: Natural language query description

        Returns:
            Dictionary with keys:
                - success: bool
                - sql: Generated SQL query
                - explanation: Query explanation
                - error: Error message (if success=False)
        """
        try:
            token = self._get_token()

            url = f"{self.api_url}/datasources/{self.datasource}/prompt"
            payload = {"question": question}
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'abra-q-token': token,
                'Cookie': f'abra-q-token={token}'
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Normalize response format to match existing interface
            return {
                'success': data.get('success', True),
                'sql': data.get('query', ''),
                'explanation': data.get('explanation', ''),
                'notes': '',  # Abra-Q doesn't provide notes field
                'error': None
            }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'sql': '',
                'explanation': '',
                'notes': '',
                'error': 'Request timeout - Abra-Q service took too long to respond'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'sql': '',
                'explanation': '',
                'notes': '',
                'error': f'Abra-Q API error: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'sql': '',
                'explanation': '',
                'notes': '',
                'error': f'Unexpected error: {str(e)}'
            }

    def get_sample_queries(self) -> Dict:
        """Fetch sample queries from Abra-Q datasource.

        Returns:
            Dictionary with sample queries or error information
        """
        try:
            token = self._get_token()

            url = f"{self.api_url}/datasources/{self.datasource}/sample-queries"
            headers = {
                'Accept': 'application/json',
                'abra-q-token': token,
                'Cookie': f'abra-q-token={token}'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            return {
                'success': True,
                'samples': response.json(),
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'samples': [],
                'error': f'Failed to fetch sample queries: {str(e)}'
            }

    def generate_new_sample_queries(self) -> Dict:
        """Request generation of new sample queries.

        Returns:
            Dictionary with new sample queries or error information
        """
        try:
            token = self._get_token()

            url = f"{self.api_url}/datasources/{self.datasource}/sample-queries"
            headers = {
                'Accept': 'application/json',
                'abra-q-token': token,
                'Cookie': f'abra-q-token={token}'
            }

            response = requests.post(url, headers=headers, timeout=30)
            response.raise_for_status()

            return {
                'success': True,
                'samples': response.json(),
                'error': None
            }

        except Exception as e:
            return {
                'success': False,
                'samples': [],
                'error': f'Failed to generate new sample queries: {str(e)}'
            }


def get_abraq_client() -> Optional[AbraQClient]:
    """Factory function to get configured Abra-Q client.

    Returns:
        AbraQClient instance if credentials are configured, None otherwise
    """
    try:
        email = os.getenv("ABRAQ_EMAIL")
        password = os.getenv("ABRAQ_PASSWORD")

        if email and password:
            return AbraQClient()
        return None

    except Exception as e:
        print(f"Error initializing Abra-Q client: {e}")
        return None


def is_abraq_available() -> bool:
    """Check if Abra-Q integration is available and configured.

    Returns:
        True if Abra-Q is properly configured, False otherwise
    """
    return get_abraq_client() is not None
