
import os
import sys
from unittest.mock import patch, MagicMock
import pytest

# Mock modules BEFORE import
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.oauth2"] = MagicMock()
sys.modules["streamlit"] = MagicMock()
sys.modules["altair"] = MagicMock()

import app

def test_get_claude_client_priority():
    """Test that st.secrets takes precedence over os.getenv."""
    
    with patch('app.st') as mock_st, \
         patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env_key'}), \
         patch('anthropic.Anthropic') as MockAnthropic:
        
        # Setup secrets to behave like a dict or access
        # Key: secrets.get returns specific value
        mock_st.secrets.get.return_value = 'secret_key'
        
        # Call function
        app.get_claude_client()
        
        # Check usage
        MockAnthropic.assert_called_with(api_key='secret_key')

def test_get_claude_client_fallback():
    """Test fallback to os.getenv if secrets missing or empty."""
    
    with patch('app.st') as mock_st, \
         patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'env_key'}), \
         patch('anthropic.Anthropic') as MockAnthropic:
        
        # Simulate secrets.get failing (FileNotFoundError or AttributeError)
        mock_st.secrets.get.side_effect = FileNotFoundError 
        
        app.get_claude_client()
        
        MockAnthropic.assert_called_with(api_key='env_key')

def test_get_claude_client_none():
    """Test returns None if no key found."""
    
    with patch('app.st') as mock_st, \
         patch.dict(os.environ, {}, clear=True), \
         patch('anthropic.Anthropic') as MockAnthropic:
        
        # Simulate secrets.get finding nothing (and secrets file existing but empty key?)
        # Or raising error
        mock_st.secrets.get.side_effect = FileNotFoundError
        
        client = app.get_claude_client()
        
        assert client is None
