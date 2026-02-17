"""Tests for dblp_offline.py functions."""

import pytest
import tempfile
import os
import sqlite3
from datetime import datetime, timezone, timedelta

from dblp_offline import (
    parse_ntriples_line,
    get_db_metadata,
    get_db_age_days,
    check_staleness,
    STALENESS_THRESHOLD_DAYS,
    DBLP_TITLE,
    DBLP_AUTHORED_BY,
    DBLP_PRIMARY_NAME,
)


class TestParseNtriplesLine:
    """Tests for N-Triples line parsing."""

    def test_parse_uri_triple(self):
        """Test parsing triple with all URIs."""
        line = '<http://example.org/s> <http://example.org/p> <http://example.org/o> .'
        subj, pred, obj = parse_ntriples_line(line)
        assert subj == "http://example.org/s"
        assert pred == "http://example.org/p"
        assert obj == "http://example.org/o"

    def test_parse_literal_object(self):
        """Test parsing triple with literal object."""
        line = '<http://example.org/s> <http://example.org/p> "Some text" .'
        subj, pred, obj = parse_ntriples_line(line)
        assert subj == "http://example.org/s"
        assert pred == "http://example.org/p"
        assert obj == "Some text"

    def test_parse_typed_literal(self):
        """Test parsing literal with type annotation."""
        line = '<http://example.org/s> <http://example.org/p> "123"^^<http://www.w3.org/2001/XMLSchema#integer> .'
        subj, pred, obj = parse_ntriples_line(line)
        assert subj == "http://example.org/s"
        assert obj == "123"

    def test_parse_language_tagged_literal(self):
        """Test parsing literal with language tag."""
        line = '<http://example.org/s> <http://example.org/p> "Hello"@en .'
        subj, pred, obj = parse_ntriples_line(line)
        assert obj == "Hello"

    def test_parse_escaped_quotes(self):
        """Test parsing literal with escaped quotes."""
        line = r'<http://example.org/s> <http://example.org/p> "Say \"hello\"" .'
        subj, pred, obj = parse_ntriples_line(line)
        assert obj == 'Say "hello"'

    def test_parse_escaped_newline(self):
        """Test parsing literal with escaped newline."""
        line = r'<http://example.org/s> <http://example.org/p> "Line1\nLine2" .'
        subj, pred, obj = parse_ntriples_line(line)
        assert "Line1\nLine2" == obj

    def test_parse_escaped_tab(self):
        """Test parsing literal with escaped tab."""
        line = r'<http://example.org/s> <http://example.org/p> "Col1\tCol2" .'
        subj, pred, obj = parse_ntriples_line(line)
        assert obj == "Col1\tCol2"

    def test_parse_escaped_backslash(self):
        """Test parsing literal with escaped backslash."""
        line = r'<http://example.org/s> <http://example.org/p> "Path\\file" .'
        subj, pred, obj = parse_ntriples_line(line)
        assert obj == r"Path\file"

    def test_parse_empty_line(self):
        """Test parsing empty line."""
        subj, pred, obj = parse_ntriples_line("")
        assert subj is None
        assert pred is None
        assert obj is None

    def test_parse_comment_line(self):
        """Test parsing comment line."""
        line = "# This is a comment"
        subj, pred, obj = parse_ntriples_line(line)
        assert subj is None

    def test_parse_whitespace_line(self):
        """Test parsing whitespace-only line."""
        subj, pred, obj = parse_ntriples_line("   ")
        assert subj is None

    def test_parse_dblp_title_predicate(self):
        """Test parsing DBLP title predicate."""
        line = f'<https://dblp.org/rec/conf/acl/SmithJ23> <{DBLP_TITLE}> "Deep Learning for NLP" .'
        subj, pred, obj = parse_ntriples_line(line)
        assert pred == DBLP_TITLE
        assert obj == "Deep Learning for NLP"

    def test_parse_dblp_authored_by(self):
        """Test parsing DBLP authoredBy predicate."""
        line = f'<https://dblp.org/rec/conf/acl/SmithJ23> <{DBLP_AUTHORED_BY}> <https://dblp.org/pid/123/4567> .'
        subj, pred, obj = parse_ntriples_line(line)
        assert pred == DBLP_AUTHORED_BY

    def test_parse_dblp_primary_name(self):
        """Test parsing DBLP primaryCreatorName predicate."""
        line = f'<https://dblp.org/pid/123/4567> <{DBLP_PRIMARY_NAME}> "John Smith" .'
        subj, pred, obj = parse_ntriples_line(line)
        assert pred == DBLP_PRIMARY_NAME
        assert obj == "John Smith"

    def test_parse_invalid_format(self):
        """Test parsing invalid N-Triples format."""
        line = "This is not valid N-Triples format"
        subj, pred, obj = parse_ntriples_line(line)
        assert subj is None


class TestGetDbMetadata:
    """Tests for database metadata retrieval."""

    def test_get_metadata_valid_db(self):
        """Test getting metadata from valid database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Create test database with metadata
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute('''
                CREATE TABLE metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            ''')
            cur.execute("INSERT INTO metadata (key, value) VALUES ('build_date', '2024-01-15T12:00:00+00:00')")
            cur.execute("INSERT INTO metadata (key, value) VALUES ('publication_count', '1000000')")
            conn.commit()
            conn.close()

            meta = get_db_metadata(db_path)
            assert meta is not None
            assert meta['build_date'] == '2024-01-15T12:00:00+00:00'
            assert meta['publication_count'] == '1000000'
        finally:
            os.unlink(db_path)

    def test_get_metadata_nonexistent_db(self):
        """Test getting metadata from nonexistent database."""
        meta = get_db_metadata('/nonexistent/path/db.db')
        assert meta is None

    def test_get_metadata_invalid_db(self):
        """Test getting metadata from invalid database."""
        import tempfile as tmp_module
        db_path = tmp_module.mktemp(suffix='.db')
        with open(db_path, 'wb') as f:
            f.write(b'not a valid sqlite database')

        try:
            meta = get_db_metadata(db_path)
            assert meta is None
        finally:
            try:
                os.unlink(db_path)
            except PermissionError:
                pass  # Windows may keep file locked


class TestGetDbAgeDays:
    """Tests for database age calculation."""

    def test_get_age_recent_db(self):
        """Test age calculation for recent database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Create database with today's date
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            now = datetime.now(timezone.utc).isoformat()
            cur.execute("INSERT INTO metadata (key, value) VALUES ('build_date', ?)", (now,))
            conn.commit()
            conn.close()

            age = get_db_age_days(db_path)
            assert age is not None
            assert age == 0  # Built today
        finally:
            os.unlink(db_path)

    def test_get_age_old_db(self):
        """Test age calculation for old database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Create database with date 45 days ago
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            old_date = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
            cur.execute("INSERT INTO metadata (key, value) VALUES ('build_date', ?)", (old_date,))
            conn.commit()
            conn.close()

            age = get_db_age_days(db_path)
            assert age is not None
            assert age >= 44  # At least 44 days (accounting for timing)
        finally:
            os.unlink(db_path)

    def test_get_age_no_build_date(self):
        """Test age calculation when build_date is missing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            cur.execute("INSERT INTO metadata (key, value) VALUES ('other_key', 'value')")
            conn.commit()
            conn.close()

            age = get_db_age_days(db_path)
            assert age is None
        finally:
            os.unlink(db_path)

    def test_get_age_nonexistent_db(self):
        """Test age calculation for nonexistent database."""
        age = get_db_age_days('/nonexistent/path/db.db')
        assert age is None


class TestCheckStaleness:
    """Tests for staleness checking."""

    def test_fresh_db_no_warning(self):
        """Test that fresh database returns no warning."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            now = datetime.now(timezone.utc).isoformat()
            cur.execute("INSERT INTO metadata (key, value) VALUES ('build_date', ?)", (now,))
            conn.commit()
            conn.close()

            warning = check_staleness(db_path)
            assert warning is None
        finally:
            os.unlink(db_path)

    def test_stale_db_returns_warning(self):
        """Test that stale database returns warning."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            old_date = (datetime.now(timezone.utc) - timedelta(days=STALENESS_THRESHOLD_DAYS + 10)).isoformat()
            cur.execute("INSERT INTO metadata (key, value) VALUES ('build_date', ?)", (old_date,))
            conn.commit()
            conn.close()

            warning = check_staleness(db_path)
            assert warning is not None
            assert "days old" in warning
            assert "--update-dblp" in warning
        finally:
            os.unlink(db_path)

    def test_staleness_threshold_defined(self):
        """Test that staleness threshold is defined."""
        assert STALENESS_THRESHOLD_DAYS == 30

    def test_unknown_age_returns_warning(self):
        """Test that unknown age returns warning."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # Create empty database with no metadata
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute('CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)')
            conn.commit()
            conn.close()

            warning = check_staleness(db_path)
            assert warning is not None
            assert "Could not determine" in warning
        finally:
            os.unlink(db_path)


class TestDBLPConstants:
    """Tests for DBLP RDF constants."""

    def test_dblp_title_predicate(self):
        """Test DBLP title predicate constant."""
        assert DBLP_TITLE == "https://dblp.org/rdf/schema#title"

    def test_dblp_authored_by_predicate(self):
        """Test DBLP authoredBy predicate constant."""
        assert DBLP_AUTHORED_BY == "https://dblp.org/rdf/schema#authoredBy"

    def test_dblp_primary_name_predicate(self):
        """Test DBLP primaryCreatorName predicate constant."""
        assert DBLP_PRIMARY_NAME == "https://dblp.org/rdf/schema#primaryCreatorName"
