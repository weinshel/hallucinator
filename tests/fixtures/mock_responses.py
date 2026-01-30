"""Mocked API responses for database query tests."""

# CrossRef API response
CROSSREF_SUCCESS = {
    "status": "ok",
    "message-type": "work-list",
    "message": {
        "items": [
            {
                "title": ["Deep Learning for Natural Language Processing"],
                "author": [
                    {"given": "John", "family": "Smith"},
                    {"given": "Alice", "family": "Jones"},
                ],
                "DOI": "10.1234/example.2023.001",
            }
        ]
    }
}

CROSSREF_NOT_FOUND = {
    "status": "ok",
    "message-type": "work-list",
    "message": {
        "items": []
    }
}

# arXiv API response (Atom XML)
ARXIV_SUCCESS = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2301.12345v1</id>
    <title>Deep Learning for Natural Language Processing</title>
    <author>
      <name>John Smith</name>
    </author>
    <author>
      <name>Alice Jones</name>
    </author>
    <link href="http://arxiv.org/abs/2301.12345v1" rel="alternate" type="text/html"/>
  </entry>
</feed>
"""

ARXIV_NOT_FOUND = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>
"""

# DBLP API response
DBLP_SUCCESS = {
    "result": {
        "hits": {
            "hit": [
                {
                    "info": {
                        "title": "Deep Learning for Natural Language Processing",
                        "authors": {
                            "author": [
                                {"text": "John Smith"},
                                {"text": "Alice Jones"},
                            ]
                        },
                        "url": "https://dblp.org/rec/conf/acl/SmithJ23"
                    }
                }
            ]
        }
    }
}

DBLP_NOT_FOUND = {
    "result": {
        "hits": {
            "hit": []
        }
    }
}

# Semantic Scholar API response
SEMANTIC_SCHOLAR_SUCCESS = {
    "data": [
        {
            "title": "Deep Learning for Natural Language Processing",
            "authors": [
                {"name": "John Smith"},
                {"name": "Alice Jones"},
            ],
            "url": "https://www.semanticscholar.org/paper/abc123"
        }
    ]
}

SEMANTIC_SCHOLAR_NOT_FOUND = {
    "data": []
}

# OpenAlex API response
OPENALEX_SUCCESS = {
    "results": [
        {
            "title": "Deep Learning for Natural Language Processing",
            "authorships": [
                {"author": {"display_name": "John Smith"}},
                {"author": {"display_name": "Alice Jones"}},
            ],
            "doi": "https://doi.org/10.1234/example.2023.001",
            "id": "https://openalex.org/W12345"
        }
    ]
}

OPENALEX_NOT_FOUND = {
    "results": []
}

# ACL Anthology HTML response
ACL_SUCCESS_HTML = """
<html>
<body>
<div class="d-sm-flex align-items-stretch p-2">
    <h5>Deep Learning for Natural Language Processing</h5>
    <span class="badge badge-light">John Smith</span>
    <span class="badge badge-light">Alice Jones</span>
    <a href="/papers/2023.acl-main.123">Paper</a>
</div>
</body>
</html>
"""

ACL_NOT_FOUND_HTML = """
<html>
<body>
<div class="no-results">No results found</div>
</body>
</html>
"""

# NeurIPS papers index HTML
NEURIPS_INDEX_HTML = """
<html>
<body>
<a href="/paper_files/paper/2023/hash/abc123-Abstract.html">Deep Learning for Natural Language Processing</a>
</body>
</html>
"""

NEURIPS_PAPER_HTML = """
<html>
<body>
<li class="author">John Smith</li>
<li class="author">Alice Jones</li>
</body>
</html>
"""

NEURIPS_NOT_FOUND_HTML = """
<html>
<body>
</body>
</html>
"""

# OpenReview API response (currently disabled but kept for reference)
OPENREVIEW_SUCCESS = {
    "notes": [
        {
            "content": {
                "title": {"value": "Deep Learning for Natural Language Processing"},
                "authors": {"value": ["John Smith", "Alice Jones"]},
            },
            "forum": "abc123xyz"
        }
    ]
}

OPENREVIEW_NOT_FOUND = {
    "notes": []
}
