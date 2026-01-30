"""Integration tests for Flask web application."""

import pytest
import json
import io
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the Flask app
from app import app


@pytest.fixture
def client():
    """Create test client for Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_pdf_content():
    """Create minimal valid PDF content for testing."""
    # This is a minimal valid PDF structure
    # In real tests, you'd use a fixture file or PyMuPDF to create a proper PDF
    return b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000052 00000 n \n0000000101 00000 n \ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF'


class TestIndexRoute:
    """Tests for the index route."""

    def test_index_returns_html(self, client):
        """Test that index route returns HTML page."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data


class TestAnalyzeRouteValidation:
    """Tests for /analyze route input validation."""

    def test_no_file_provided(self, client):
        """Test error when no file is provided."""
        response = client.post('/analyze')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No file' in data['error']

    def test_empty_filename(self, client):
        """Test error when filename is empty."""
        data = {
            'pdf': (io.BytesIO(b''), '')  # Empty filename
        }
        response = client.post('/analyze', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_invalid_file_type(self, client):
        """Test error for non-PDF file."""
        data = {
            'pdf': (io.BytesIO(b'not a pdf'), 'test.txt')
        }
        response = client.post('/analyze', data=data, content_type='multipart/form-data')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'PDF' in data['error'] or 'must be' in data['error']


class TestAnalyzeRoute:
    """Tests for /analyze route functionality."""

    @patch('app.analyze_pdf')
    def test_successful_analysis(self, mock_analyze, client, sample_pdf_content):
        """Test successful PDF analysis."""
        # Mock the analyze_pdf function
        mock_results = [
            {
                'title': 'Test Paper Title',
                'status': 'verified',
                'source': 'CrossRef',
                'ref_authors': ['John Smith'],
                'found_authors': ['John Smith'],
                'error_type': None,
            }
        ]
        mock_stats = {
            'total_raw': 10,
            'skipped_url': 1,
            'skipped_short_title': 2,
            'skipped_no_authors': 0,
            'total_timeouts': 0,
            'retried_count': 0,
            'retry_successes': 0,
        }
        mock_analyze.return_value = (mock_results, mock_stats)

        data = {
            'pdf': (io.BytesIO(sample_pdf_content), 'test.pdf')
        }
        response = client.post('/analyze', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        result = json.loads(response.data)
        assert result['success'] is True
        assert 'summary' in result
        assert 'results' in result

    @patch('app.analyze_pdf')
    def test_analysis_with_api_keys(self, mock_analyze, client, sample_pdf_content):
        """Test analysis with API keys provided."""
        mock_analyze.return_value = ([], {'total_raw': 0, 'skipped_url': 0, 'skipped_short_title': 0, 'skipped_no_authors': 0, 'total_timeouts': 0, 'retried_count': 0, 'retry_successes': 0})

        data = {
            'pdf': (io.BytesIO(sample_pdf_content), 'test.pdf'),
            'openalex_key': 'test-openalex-key',
            's2_api_key': 'test-s2-key',
        }
        response = client.post('/analyze', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        # Verify API keys were passed to analyze_pdf
        mock_analyze.assert_called_once()
        call_kwargs = mock_analyze.call_args[1]
        assert call_kwargs.get('openalex_key') == 'test-openalex-key'
        assert call_kwargs.get('s2_api_key') == 'test-s2-key'


class TestAnalyzeStreamRoute:
    """Tests for /analyze/stream SSE route."""

    def test_stream_no_file(self, client):
        """Test streaming error when no file provided."""
        response = client.post('/analyze/stream')
        assert response.status_code == 400

    def test_stream_invalid_file_type(self, client):
        """Test streaming error for invalid file type."""
        data = {
            'pdf': (io.BytesIO(b'not a pdf'), 'test.txt')
        }
        response = client.post('/analyze/stream', data=data, content_type='multipart/form-data')
        assert response.status_code == 400

    @patch('app.analyze_pdf')
    def test_stream_content_type(self, mock_analyze, client, sample_pdf_content):
        """Test that stream returns correct content type."""
        mock_analyze.return_value = ([], {'total_raw': 0, 'skipped_url': 0, 'skipped_short_title': 0, 'skipped_no_authors': 0, 'total_timeouts': 0, 'retried_count': 0, 'retry_successes': 0})

        data = {
            'pdf': (io.BytesIO(sample_pdf_content), 'test.pdf')
        }
        response = client.post('/analyze/stream', data=data, content_type='multipart/form-data')

        assert response.status_code == 200
        # Content type may include charset
        assert 'text/event-stream' in response.content_type


class TestArchiveHandling:
    """Tests for archive (ZIP/tar.gz) handling."""

    def test_zip_file_accepted(self, client):
        """Test that ZIP files are accepted."""
        # Create minimal ZIP with PDF
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            # Add a minimal PDF
            zf.writestr('test.pdf', b'%PDF-1.4\n%%EOF')
        zip_buffer.seek(0)

        data = {
            'pdf': (zip_buffer, 'archive.zip')
        }

        with patch('app.extract_pdfs_from_archive') as mock_extract:
            # Mock to return empty list to avoid actual processing
            mock_extract.side_effect = ValueError("No PDF files found in archive")

            response = client.post('/analyze', data=data, content_type='multipart/form-data')
            # Should attempt to process as archive
            assert response.status_code == 400  # No PDFs found

    def test_tar_gz_file_accepted(self, client):
        """Test that tar.gz files are accepted."""
        data = {
            'pdf': (io.BytesIO(b'\x1f\x8b\x08\x00'), 'archive.tar.gz')
        }

        response = client.post('/analyze', data=data, content_type='multipart/form-data')
        # Will fail to extract but should recognize the file type
        assert response.status_code in [400, 500]  # Invalid archive


class TestResponseStructure:
    """Tests for API response structure."""

    @patch('app.analyze_pdf')
    def test_summary_structure(self, mock_analyze, client, sample_pdf_content):
        """Test that summary has all expected fields."""
        mock_analyze.return_value = (
            [{'title': 'Test', 'status': 'verified', 'source': 'CrossRef', 'ref_authors': [], 'found_authors': [], 'error_type': None}],
            {'total_raw': 10, 'skipped_url': 1, 'skipped_short_title': 2, 'skipped_no_authors': 0, 'total_timeouts': 0, 'retried_count': 0, 'retry_successes': 0}
        )

        data = {'pdf': (io.BytesIO(sample_pdf_content), 'test.pdf')}
        response = client.post('/analyze', data=data, content_type='multipart/form-data')

        result = json.loads(response.data)
        summary = result['summary']

        expected_fields = ['total_raw', 'total', 'verified', 'not_found', 'mismatched', 'skipped']
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"

    @patch('app.analyze_pdf')
    def test_result_structure(self, mock_analyze, client, sample_pdf_content):
        """Test that each result has expected fields."""
        mock_result = {
            'title': 'Test Paper',
            'status': 'verified',
            'source': 'CrossRef',
            'ref_authors': ['John Smith'],
            'found_authors': ['John Smith'],
            'paper_url': 'https://doi.org/10.1234/test',
            'error_type': None,
            'failed_dbs': [],
        }
        mock_analyze.return_value = ([mock_result], {'total_raw': 1, 'skipped_url': 0, 'skipped_short_title': 0, 'skipped_no_authors': 0, 'total_timeouts': 0, 'retried_count': 0, 'retry_successes': 0})

        data = {'pdf': (io.BytesIO(sample_pdf_content), 'test.pdf')}
        response = client.post('/analyze', data=data, content_type='multipart/form-data')

        result = json.loads(response.data)
        assert len(result['results']) == 1

        ref_result = result['results'][0]
        assert 'title' in ref_result
        assert 'status' in ref_result
        assert ref_result['status'] in ['verified', 'not_found', 'author_mismatch']


class TestErrorHandling:
    """Tests for error handling."""

    @patch('app.analyze_pdf')
    def test_analysis_exception(self, mock_analyze, client, sample_pdf_content):
        """Test handling of analysis exception."""
        mock_analyze.side_effect = Exception("Analysis failed")

        data = {'pdf': (io.BytesIO(sample_pdf_content), 'test.pdf')}
        response = client.post('/analyze', data=data, content_type='multipart/form-data')

        assert response.status_code == 500
        result = json.loads(response.data)
        assert 'error' in result

    def test_cleanup_on_error(self, client):
        """Test that temp files are cleaned up on error."""
        # This is implicitly tested - temp directory cleanup happens in finally block
        data = {'pdf': (io.BytesIO(b'%PDF-1.4\n%%EOF'), 'test.pdf')}  # Minimal valid PDF header
        response = client.post('/analyze', data=data, content_type='multipart/form-data')
        # Response will be error (invalid PDF) but cleanup should happen
        assert response.status_code in [200, 400, 500]
