import pytest
from django.urls import reverse
from rest_framework.test import APIClient

@pytest.mark.django_db
def test_api_root_or_docs_endpoint():
    """
    Test that the Django application loads and the API docs schema endpoint is reachable.
    """
    client = APIClient()
    # Using drf-spectacular schema endpoint as a health check
    response = client.get('/api/schema/')
    # As long as the schema generates or redirects, Django is healthy
    assert response.status_code in [200, 301, 302]

def test_basic_math():
    """
    A simple sanity check to ensure pytest is running correctly.
    """
    assert 2 + 2 == 4
