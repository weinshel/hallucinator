"""Shared pytest fixtures for all tests."""

import os
import pytest
from pathlib import Path


@pytest.fixture
def ieee_reference():
    """Sample IEEE format reference."""
    return 'J. Smith and A. Jones, "Deep Learning for Natural Language Processing," in Proc. ACL, 2023.'


@pytest.fixture
def acm_reference():
    """Sample ACM format reference."""
    return 'John Smith, Alice Jones, and Bob Williams. 2023. Deep Learning for Natural Language Processing. In Proceedings of the ACL Conference.'


@pytest.fixture
def usenix_reference():
    """Sample USENIX format reference."""
    return 'John Smith and Alice Jones. Deep Learning for Natural Language Processing. In USENIX Security Symposium, 2023.'


@pytest.fixture
def aaai_reference():
    """Sample AAAI format reference."""
    return 'Smith, J.; Jones, A.; and Williams, C. 2023. Deep Learning for Natural Language Processing. AAAI 37(1).'


@pytest.fixture
def em_dash_reference():
    """Reference using em-dash for same authors as previous."""
    return '——, "Another Paper by Same Authors," in Proc. ICML, 2023.'


@pytest.fixture
def test_data_dir():
    """Path to test-data directory."""
    return Path(__file__).parent.parent / "test-data"


@pytest.fixture
def test_pdf_path(test_data_dir):
    """Path to a test PDF file if it exists."""
    pdf_path = test_data_dir / "hallucinated.pdf"
    if pdf_path.exists():
        return pdf_path
    # Return None if not found (test will skip)
    return None


@pytest.fixture
def sample_references_text():
    """Sample references section text for testing segmentation."""
    return """
References

[1] J. Smith and A. Jones, "Deep Learning for Natural Language Processing," in Proc. ACL, 2023.

[2] M. Chen, B. Lee, and C. Wang, "Transformer Models for Text Classification," IEEE Trans. Neural Networks, vol. 15, no. 3, pp. 234-256, 2022.

[3] A. Brown, "A Survey of Machine Learning Methods," in Proc. International Conference on Machine Learning, 2021.
"""


@pytest.fixture
def sample_references_aaai_text():
    """Sample AAAI-style references section text."""
    return """
References

Smith, J.; Jones, A.; and Williams, C. 2023. Deep Learning for Natural Language Processing. AAAI 37(1).
Chen, M.; Lee, B.; and Wang, C. 2022. Transformer Models for Text Classification. AAAI 36(5).
Brown, A. 2021. A Survey of Machine Learning Methods. AAAI 35(2).
"""


@pytest.fixture
def sample_references_numbered_text():
    """Sample numbered-style references section text."""
    return """
References

1. J. Smith and A. Jones, "Deep Learning for Natural Language Processing," in Proc. ACL, 2023.

2. M. Chen, B. Lee, and C. Wang, "Transformer Models for Text Classification," IEEE Trans. Neural Networks, vol. 15, no. 3, pp. 234-256, 2022.

3. A. Brown, "A Survey of Machine Learning Methods," in Proc. International Conference on Machine Learning, 2021.
"""


@pytest.fixture
def ligature_text():
    """Text containing common PDF ligatures."""
    return "This is a ﬁne ﬁle with ﬂuid ﬀects and eﬃcient eﬄuent ﬅrange ﬆuff."


@pytest.fixture
def hyphenated_text():
    """Text with hyphenation that needs fixing."""
    return """This paper describes a method for detec-
tion of human-
centered design patterns using machine learning tech-
niques."""
