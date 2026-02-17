"""Sample reference strings by format for testing."""

# IEEE format: J. Smith, A. Jones, and C. Williams, "Title," in Venue, Year.
IEEE_REFERENCES = [
    (
        'J. Smith and A. Jones, "Deep Learning for Natural Language Processing," in Proc. ACL, 2023.',
        {
            'expected_title': 'Deep Learning for Natural Language Processing',
            'expected_authors': ['J. Smith', 'A. Jones'],
        }
    ),
    (
        'M. Chen, B. Lee, C. Wang, and D. Kim, "Transformer Models for Text Classification," IEEE Trans. Neural Networks, vol. 15, no. 3, pp. 234-256, 2022.',
        {
            'expected_title': 'Transformer Models for Text Classification',
            'expected_authors': ['M. Chen', 'B. Lee', 'C. Wang', 'D. Kim'],
        }
    ),
    (
        'A. Brown, "A Survey of Machine Learning Methods," in Proc. International Conference on Machine Learning, 2021.',
        {
            'expected_title': 'A Survey of Machine Learning Methods',
            'expected_authors': ['A. Brown'],
        }
    ),
]

# ACM format: FirstName LastName, FirstName LastName, and FirstName LastName. Year. Title. In Venue.
ACM_REFERENCES = [
    (
        'John Smith, Alice Jones, and Bob Williams. 2023. Deep Learning for Natural Language Processing. In Proceedings of the ACL Conference.',
        {
            'expected_title': 'Deep Learning for Natural Language Processing',
            'expected_authors': ['John Smith', 'Alice Jones', 'Bob Williams'],
        }
    ),
    (
        'Maria Garcia and Carlos Rodriguez. 2022. Neural Networks for Image Recognition. In CHI Conference on Human Factors in Computing Systems.',
        {
            'expected_title': 'Neural Networks for Image Recognition',
            'expected_authors': ['Maria Garcia', 'Carlos Rodriguez'],
        }
    ),
]

# USENIX format: FirstName LastName and FirstName LastName. Title. In Venue, Year.
USENIX_REFERENCES = [
    (
        'John Smith and Alice Jones. Deep Learning for Natural Language Processing. In USENIX Security Symposium, 2023.',
        {
            'expected_title': 'Deep Learning for Natural Language Processing',
            'expected_authors': ['John Smith', 'Alice Jones'],
        }
    ),
    (
        'Robert Chen. Secure Systems Design Principles. In Proceedings of the USENIX Annual Technical Conference, 2022.',
        {
            'expected_title': 'Secure Systems Design Principles',
            'expected_authors': ['Robert Chen'],
        }
    ),
]

# AAAI format: Surname, I.; Surname, I.; and Surname, I. Year. Title. Venue.
AAAI_REFERENCES = [
    (
        'Smith, J.; Jones, A.; and Williams, C. 2023. Deep Learning for Natural Language Processing. AAAI 37(1).',
        {
            'expected_title': 'Deep Learning for Natural Language Processing',
            'expected_authors': ['Smith, J.', 'Jones, A.', 'Williams, C.'],
        }
    ),
    (
        'Bail, C. A.; Argyle, L. P.; and Brown, T. W. 2022. Exposure to Opposing Views. Proceedings of the National Academy of Sciences 115(37).',
        {
            'expected_title': 'Exposure to Opposing Views',
            'expected_authors': ['Bail, C. A.', 'Argyle, L. P.', 'Brown, T. W.'],
        }
    ),
]

# Compound surnames
COMPOUND_SURNAME_REFERENCES = [
    (
        'Van Bavel, J.; Jones, A.; and Williams, C. 2023. Social Identity and Political Polarization. PNAS 120(15).',
        {
            'expected_title': 'Social Identity and Political Polarization',
            'expected_authors': ['Van Bavel, J.', 'Jones, A.', 'Williams, C.'],
        }
    ),
    (
        'Camacho-Collados, J. and Pilehvar, M. T. 2020. On the Role of Text Preprocessing. In Proceedings of ACL.',
        {
            'expected_title': 'On the Role of Text Preprocessing',
            'expected_authors': ['Camacho-Collados, J.', 'Pilehvar, M. T.'],
        }
    ),
    (
        'Del Vicario, M.; Bessi, A.; and Zollo, F. 2016. The Spreading of Misinformation Online. PNAS 113(3).',
        {
            'expected_title': 'The Spreading of Misinformation Online',
            'expected_authors': ['Del Vicario, M.', 'Bessi, A.', 'Zollo, F.'],
        }
    ),
]

# Em-dash pattern (same authors as previous)
EM_DASH_REFERENCES = [
    (
        '——, "Another Paper by Same Authors," in Proc. ICML, 2023.',
        {
            'expected_title': 'Another Paper by Same Authors',
            'expected_authors': ['__SAME_AS_PREVIOUS__'],
        }
    ),
    (
        '———, "Yet Another Paper," in Proc. NeurIPS, 2022.',
        {
            'expected_title': 'Yet Another Paper',
            'expected_authors': ['__SAME_AS_PREVIOUS__'],
        }
    ),
]

# Et al. references
ET_AL_REFERENCES = [
    (
        'Smith, J. et al. 2023. Large-Scale Analysis of Social Media. Nature Communications 14(1).',
        {
            'expected_title': 'Large-Scale Analysis of Social Media',
            'expected_authors': ['Smith, J.'],  # et al. should be removed
        }
    ),
    (
        'A. Jones et al., "Distributed Computing Framework," in Proc. SOSP, 2022.',
        {
            'expected_title': 'Distributed Computing Framework',
            'expected_authors': ['A. Jones'],
        }
    ),
]

# References with smart quotes
SMART_QUOTE_REFERENCES = [
    (
        'J. Smith, \u201cDeep Learning for NLP,\u201d in Proc. ACL, 2023.',  # Unicode smart quotes
        {
            'expected_title': 'Deep Learning for NLP',
            'expected_authors': ['J. Smith'],
        }
    ),
]

# References with subtitle after colon
SUBTITLE_REFERENCES = [
    (
        'J. Smith, "Main Title": A Comprehensive Survey, in Proc. ACL, 2023.',
        {
            'expected_title': 'Main Title: A Comprehensive Survey',
            'expected_authors': ['J. Smith'],
        }
    ),
]

# Short titles that should be skipped (<5 words)
SHORT_TITLE_REFERENCES = [
    (
        'J. Smith, "Deep Learning," in Proc. ACL, 2023.',
        {
            'expected_title': 'Deep Learning',  # Only 2 words
            'should_skip': True,
        }
    ),
]

# Non-academic URL references that should be skipped
URL_REFERENCES = [
    (
        'GitHub Repository. https://github.com/example/repo',
        {
            'should_skip': True,
            'reason': 'non-academic URL',
        }
    ),
    (
        'PyTorch Documentation. https://pytorch.org/docs/stable/',
        {
            'should_skip': True,
            'reason': 'non-academic URL',
        }
    ),
    # Academic URLs should NOT be skipped
    (
        'Smith, J. 2023. Deep Learning Methods. arXiv:2301.12345. https://arxiv.org/abs/2301.12345',
        {
            'should_skip': False,
            'reason': 'academic URL (arxiv)',
        }
    ),
]
