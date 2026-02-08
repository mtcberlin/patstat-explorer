"""
PATSTAT Queries - Numbered queries with stakeholder tags.
BigQuery syntax for EPO PATSTAT on Google BigQuery.

Structure:
- QUERIES: Dict with query ID (Q01, Q02, ...) as key
- Each query has: title, tags, description, explanation, key_outputs, timing, sql, sql_template, parameters
- sql_template: Parameterized version using @param placeholders for dynamic queries
- parameters: Dict defining which parameters this query accepts (query-specific)
- STAKEHOLDERS: Available stakeholder tags for filtering

Parameter System (Story 1.8):
Each query defines its own 'parameters' dict specifying which inputs it accepts.
The frontend renders only the controls relevant to each query.

Parameter Schema:
    "parameters": {
        "param_name": {
            "type": "year_range" | "multiselect" | "select" | "text",
            "label": "Display Label",
            "options": [...] | "jurisdictions" | "wipo_fields",  # for select/multiselect
            "defaults": [...] | value,
            "default_start": int,  # for year_range only
            "default_end": int,    # for year_range only
            "required": True | False
        }
    }

Available Parameter Types:
- year_range: Year slider with default_start and default_end
- multiselect: Multiple selection dropdown (options can be list or "jurisdictions"/"wipo_fields")
- select: Single selection dropdown
- text: Text input field

SQL Parameter Placeholders (used in sql_template):
- @year_start, @year_end: INT64 - Year range filter
- @jurisdictions: ARRAY<STRING> - List of patent office codes
- @tech_field: INT64 - WIPO technology field number
"""

# Available stakeholder tags
STAKEHOLDERS = {
    "PATLIB": "Patent Information Centers & Libraries",
    "BUSINESS": "Companies & Industry",
    "UNIVERSITY": "Universities & Research",
}

QUERIES = {
    # =========================================================================
    # OVERVIEW / DATABASE EXPLORATION (Q01-Q05)
    # =========================================================================
    "Q01": {
        "title": "What are the overall PATSTAT database statistics?",
        "tags": ["PATLIB"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Comprehensive PATSTAT database statistics: applications, grants, publications, families, and more",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 1782,
                "default_end": 2024,
                "required": False
            }
        },
        "explanation": """Comprehensive statistics about the PATSTAT database:
- Total patent applications and granted patents
- Date range coverage (earliest to latest filing year)
- Publications and patent families
- Unique persons (applicants/inventors)
- CPC classifications, citations, and legal events

Essential for understanding the scope and coverage of the database.""",
        "key_outputs": [
            "Total patent applications",
            "Granted patents",
            "Earliest/Latest filing year",
            "Publications",
            "Patent families",
            "Unique persons",
            "CPC symbols assigned",
            "Citations",
            "Legal events"
        ],
        "estimated_seconds_first_run": 15,
        "estimated_seconds_cached": 5,
        "display_mode": "metrics_grid",
        "sql": """
            SELECT 'Total Applications' AS metric, CAST(COUNT(*) AS STRING) AS value FROM `tls201_appln`
            UNION ALL
            SELECT 'Granted Patents', CAST(COUNT(*) AS STRING) FROM `tls201_appln` WHERE granted = 'Y'
            UNION ALL
            SELECT 'Earliest Filing Year', CAST(MIN(appln_filing_year) AS STRING) FROM `tls201_appln` WHERE appln_filing_year > 0
            UNION ALL
            SELECT 'Latest Filing Year', CAST(MAX(appln_filing_year) AS STRING) FROM `tls201_appln`
            UNION ALL
            SELECT 'Publications', CAST(COUNT(*) AS STRING) FROM `tls211_pat_publn`
            UNION ALL
            SELECT 'Patent Families', CAST(COUNT(DISTINCT docdb_family_id) AS STRING) FROM `tls201_appln` WHERE docdb_family_id > 0
            UNION ALL
            SELECT 'Unique Persons', CAST(COUNT(*) AS STRING) FROM `tls206_person`
            UNION ALL
            SELECT 'CPC Symbols Assigned', CAST(COUNT(*) AS STRING) FROM `tls224_appln_cpc`
            UNION ALL
            SELECT 'Citations', CAST(COUNT(*) AS STRING) FROM `tls212_citation`
            UNION ALL
            SELECT 'Legal Events', CAST(COUNT(*) AS STRING) FROM `tls231_inpadoc_legal_event`
        """,
        "sql_template": """
            SELECT 'Total Applications' AS metric, CAST(COUNT(*) AS STRING) AS value
            FROM `tls201_appln` WHERE appln_filing_year BETWEEN @year_start AND @year_end
            UNION ALL
            SELECT 'Granted Patents', CAST(COUNT(*) AS STRING)
            FROM `tls201_appln` WHERE granted = 'Y' AND appln_filing_year BETWEEN @year_start AND @year_end
            UNION ALL
            SELECT 'Earliest Filing Year', CAST(MIN(appln_filing_year) AS STRING)
            FROM `tls201_appln` WHERE appln_filing_year BETWEEN @year_start AND @year_end AND appln_filing_year > 0
            UNION ALL
            SELECT 'Latest Filing Year', CAST(MAX(appln_filing_year) AS STRING)
            FROM `tls201_appln` WHERE appln_filing_year BETWEEN @year_start AND @year_end
            UNION ALL
            SELECT 'Publications', CAST(COUNT(*) AS STRING)
            FROM `tls211_pat_publn` p
            JOIN `tls201_appln` a ON p.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
            UNION ALL
            SELECT 'Patent Families', CAST(COUNT(DISTINCT docdb_family_id) AS STRING)
            FROM `tls201_appln` WHERE docdb_family_id > 0 AND appln_filing_year BETWEEN @year_start AND @year_end
            UNION ALL
            SELECT 'Unique Persons', CAST(COUNT(DISTINCT pa.person_id) AS STRING)
            FROM tls207_pers_appln pa
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
            UNION ALL
            SELECT 'CPC Symbols Assigned', CAST(COUNT(*) AS STRING)
            FROM `tls224_appln_cpc` c
            JOIN `tls201_appln` a ON c.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
            UNION ALL
            SELECT 'Citations', CAST(COUNT(*) AS STRING)
            FROM `tls212_citation` cit
            JOIN `tls211_pat_publn` p ON cit.pat_publn_id = p.pat_publn_id
            JOIN `tls201_appln` a ON p.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
            UNION ALL
            SELECT 'Legal Events', CAST(COUNT(*) AS STRING)
            FROM `tls231_inpadoc_legal_event` le
            JOIN `tls201_appln` a ON le.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
        """
    },

    "Q02": {
        "title": "Which patent offices are most active?",
        "tags": ["PATLIB"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "Patent offices (filing authorities) in the database with application counts",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": False
            }
        },
        "explanation": """Shows all patent offices/filing authorities in PATSTAT with their application volumes.
Helps understand which patent offices are represented and their relative importance.

EP = European Patent Office, US = USPTO, CN = CNIPA, etc.""",
        "key_outputs": [
            "Filing authority codes",
            "Application counts per office",
            "Percentage of total applications"
        ],
        "estimated_seconds_first_run": 1,
        "estimated_seconds_cached": 1,
        "visualization": {
            "x": "filing_authority",
            "y": "application_count",
            "type": "bar"
        },
        "sql": """
            SELECT
                appln_auth AS filing_authority,
                COUNT(*) AS application_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
            FROM tls201_appln
            WHERE appln_auth IS NOT NULL
            GROUP BY appln_auth
            ORDER BY application_count DESC
            LIMIT 30
        """,
        "sql_template": """
            SELECT
                appln_auth AS filing_authority,
                COUNT(*) AS application_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage
            FROM tls201_appln
            WHERE appln_auth IS NOT NULL
              AND appln_filing_year BETWEEN @year_start AND @year_end
            GROUP BY appln_auth
            ORDER BY application_count DESC
            LIMIT 30
        """
    },

    "Q03": {
        "title": "How have patent applications changed over time?",
        "tags": ["PATLIB"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Patent application trends over time showing granted vs pending/rejected",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Shows the distribution of patent applications across filing years,
broken down by grant status (Granted vs Not Granted).

Note: Recent years may show lower grant rates due to:
- Publication delays (18 months from filing)
- Pending examination (can take 3-5 years)""",
        "key_outputs": [
            "Applications per year",
            "Granted vs Not Granted breakdown",
            "Grant rate percentage"
        ],
        "estimated_seconds_first_run": 3,
        "estimated_seconds_cached": 1,
        "visualization": {
            "x": "filing_year",
            "y": "count",
            "color": "status",
            "type": "stacked_bar",
            "stacked_columns": ["granted", "not_granted"]
        },
        "sql": """
            SELECT
                appln_filing_year AS filing_year,
                COUNT(*) AS applications,
                COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted,
                COUNT(CASE WHEN granted != 'Y' OR granted IS NULL THEN 1 END) AS not_granted,
                ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS grant_rate_pct
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN 1980 AND 2024
            GROUP BY appln_filing_year
            ORDER BY appln_filing_year ASC
        """,
        "sql_template": """
            SELECT
                appln_filing_year AS filing_year,
                COUNT(*) AS applications,
                COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted,
                COUNT(CASE WHEN granted != 'Y' OR granted IS NULL THEN 1 END) AS not_granted,
                ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS grant_rate_pct
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN @year_start AND @year_end
              AND appln_auth IN UNNEST(@jurisdictions)
            GROUP BY appln_filing_year
            ORDER BY appln_filing_year ASC
        """
    },

    "Q04": {
        "title": "What are the most common technology classes?",
        "tags": ["PATLIB"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Most common IPC technology classes in the database",
        "todo": "Add IPC text description, not only the symbol",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Shows the most frequently assigned IPC (International Patent Classification) classes.
IPC classes indicate the technology area of a patent:
- A: Human Necessities (medical, agriculture)
- B: Operations/Transport (vehicles, printing)
- C: Chemistry/Metallurgy
- D: Textiles/Paper
- E: Fixed Constructions
- F: Mechanical Engineering
- G: Physics (computing, optics)
- H: Electricity (electronics, communication)""",
        "key_outputs": [
            "Top IPC classes by frequency",
            "Application counts per class",
            "Technology distribution"
        ],
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                SUBSTR(ipc_class_symbol, 1, 4) AS ipc_class,
                COUNT(*) AS assignment_count,
                COUNT(DISTINCT appln_id) AS unique_applications,
                ROUND(COUNT(DISTINCT appln_id) * 100.0 / (SELECT COUNT(DISTINCT appln_id) FROM tls209_appln_ipc), 2) AS pct_of_applications
            FROM tls209_appln_ipc
            GROUP BY SUBSTR(ipc_class_symbol, 1, 4)
            ORDER BY assignment_count DESC
            LIMIT 25
        """,
        "sql_template": """
            WITH filtered_apps AS (
                SELECT DISTINCT a.appln_id
                FROM tls201_appln a
                WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND a.appln_auth IN UNNEST(@jurisdictions)
            )
            SELECT
                SUBSTR(ipc.ipc_class_symbol, 1, 4) AS ipc_class,
                COUNT(*) AS assignment_count,
                COUNT(DISTINCT ipc.appln_id) AS unique_applications
            FROM tls209_appln_ipc ipc
            JOIN filtered_apps fa ON ipc.appln_id = fa.appln_id
            GROUP BY SUBSTR(ipc.ipc_class_symbol, 1, 4)
            ORDER BY assignment_count DESC
            LIMIT 25
        """
    },

    "Q05": {
        "title": "What do sample patent records look like?",
        "tags": ["PATLIB"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Sample of 100 patent applications with key fields",
        "todo": "Extend table with more data: applicant count, inventor count, title",
        "visualization": None,
        "parameters": {},
        "explanation": """Returns a sample of patent applications to understand the data structure
and available fields in the main application table (tls201_appln).

This is the central table in PATSTAT - most queries start here.
No parameters needed - this shows recent sample data.""",
        "key_outputs": [
            "Application IDs and dates",
            "Filing authority codes",
            "Grant status",
            "Family information"
        ],
        "estimated_seconds_first_run": 1,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                appln_id,
                appln_auth,
                appln_nr,
                appln_filing_date,
                appln_filing_year,
                granted,
                docdb_family_id,
                docdb_family_size,
                nb_citing_docdb_fam,
                earliest_filing_date
            FROM tls201_appln
            WHERE appln_filing_year >= 2020
            LIMIT 100
        """,
        "sql_template": """
            SELECT
                appln_id,
                appln_auth,
                appln_nr,
                appln_filing_date,
                appln_filing_year,
                granted,
                docdb_family_id,
                docdb_family_size,
                nb_citing_docdb_fam,
                earliest_filing_date
            FROM tls201_appln
            WHERE appln_filing_year >= 2020
            LIMIT 100
        """
    },

    # =========================================================================
    # STRATEGIC / MARKET INTELLIGENCE (Q06-Q07)
    # =========================================================================
    "Q06": {
        "title": "Which countries lead in patent filing activity?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Which countries have the highest patent application activity?",
        "todo": "Fix: query mixes person_ctry_code (applicant origin) with appln_auth filter (patent office). Clarify intent: applicants from country X, or filings at office X?",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """This query analyzes patent filing activity by applicant country,
calculating both total applications and grant rates. It identifies which countries are most active
in patenting and how successful their applications are. The grant_rate metric helps assess the
quality/success of applications from different regions.

Minimum threshold of 100 patents ensures statistical relevance.""",
        "key_outputs": [
            "Country ranking by patent volume",
            "Grant rates by country (quality indicator)",
            "Total vs. granted patent counts"
        ],
        "estimated_seconds_first_run": 5,
        "estimated_seconds_cached": 1,
        "visualization": {
            "x": "person_ctry_code",
            "y": "patent_count",
            "type": "bar"
        },
        "sql": """
            SELECT
                p.person_ctry_code,
                COUNT(DISTINCT a.appln_id) AS patent_count,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted_count,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      COUNT(DISTINCT a.appln_id), 2) AS grant_rate
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND a.appln_filing_year >= 2015
              AND p.person_ctry_code IS NOT NULL
            GROUP BY p.person_ctry_code
            HAVING COUNT(DISTINCT a.appln_id) >= 100
            ORDER BY patent_count DESC
            LIMIT 20
        """,
        "sql_template": """
            SELECT
                p.person_ctry_code,
                COUNT(DISTINCT a.appln_id) AS patent_count,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted_count,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      COUNT(DISTINCT a.appln_id), 2) AS grant_rate
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND p.person_ctry_code IS NOT NULL
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY p.person_ctry_code
            HAVING COUNT(DISTINCT a.appln_id) >= 100
            ORDER BY patent_count DESC
            LIMIT 20
        """
    },

    "Q07": {
        "title": "What are the green technology trends by country?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Patent activity with green technology (CPC Y02) focus by country",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Countries to Analyze",
                "options": "jurisdictions",
                "defaults": ["US", "DE", "JP", "CN", "KR", "FR", "GB"],
                "required": True
            }
        },
        "explanation": """This query tracks patent activity trends by country,
with a special focus on green/environmental technologies (CPC Y02 class).
The Y02 class covers climate change mitigation technologies, making this
useful for ESG reporting and sustainability assessments.

Tracks both total applications and the proportion dedicated to green tech.""",
        "key_outputs": [
            "Yearly patent trends by country",
            "Green technology patent counts (Y02 class)",
            "Green tech percentage (sustainability indicator)"
        ],
        "estimated_seconds_first_run": 5,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                a.appln_filing_year,
                c.ctry_code,
                c.st3_name AS country_name,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                COUNT(DISTINCT CASE WHEN cpc.cpc_class_symbol LIKE 'Y02%' THEN a.appln_id END) AS green_tech_patents,
                ROUND(COUNT(DISTINCT CASE WHEN cpc.cpc_class_symbol LIKE 'Y02%' THEN a.appln_id END) * 100.0 /
                      COUNT(DISTINCT a.appln_id), 2) AS green_tech_percentage
            FROM tls201_appln a
            JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls801_country c ON p.person_ctry_code = c.ctry_code
            LEFT JOIN tls224_appln_cpc cpc ON a.appln_id = cpc.appln_id
            WHERE a.appln_filing_year BETWEEN 2015 AND 2022
              AND pa.applt_seq_nr > 0
              AND c.ctry_code IN ('US', 'DE', 'JP', 'CN', 'KR', 'FR', 'GB')
            GROUP BY a.appln_filing_year, c.ctry_code, c.st3_name
            ORDER BY a.appln_filing_year DESC, green_tech_percentage DESC
        """,
        "sql_template": """
            SELECT
                a.appln_filing_year,
                c.ctry_code,
                c.st3_name AS country_name,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                COUNT(DISTINCT CASE WHEN cpc.cpc_class_symbol LIKE 'Y02%' THEN a.appln_id END) AS green_tech_patents,
                ROUND(COUNT(DISTINCT CASE WHEN cpc.cpc_class_symbol LIKE 'Y02%' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 2) AS green_tech_percentage
            FROM tls201_appln a
            JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls801_country c ON p.person_ctry_code = c.ctry_code
            LEFT JOIN tls224_appln_cpc cpc ON a.appln_id = cpc.appln_id
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
              AND pa.applt_seq_nr > 0
              AND p.person_ctry_code IN UNNEST(@jurisdictions)
            GROUP BY a.appln_filing_year, c.ctry_code, c.st3_name
            ORDER BY a.appln_filing_year ASC, green_tech_percentage DESC
        """
    },

    # =========================================================================
    # TECHNOLOGY SCOUTING (Q08-Q10)
    # =========================================================================
    "Q08": {
        "title": "Which technology fields are most active?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Most active technology fields with family size and citation impact",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            },
            "tech_sector": {
                "type": "select",
                "label": "Technology Sector",
                "options": ["All Sectors", "Electrical engineering", "Instruments", "Chemistry", "Mechanical engineering", "Other fields"],
                "defaults": "All Sectors",
                "required": False
            }
        },
        "explanation": """This query uses WIPO technology field classifications to identify the most
active technology sectors. The weight filter (>0.5) ensures only primary
technology assignments are counted. Family size indicates geographic filing
breadth (patent importance), while citation counts measure technical influence.""",
        "key_outputs": [
            "Technology fields ranked by activity",
            "Average family size (geographic reach indicator)",
            "Average citations (impact/importance indicator)"
        ],
        "estimated_seconds_first_run": 14,
        "estimated_seconds_cached": 1,
        "visualization": {
            "x": "techn_field",
            "y": "application_count",
            "color": "techn_sector",
            "type": "bar"
        },
        "sql": """
            SELECT
                tf.techn_field,
                tf.techn_sector,
                COUNT(DISTINCT a.appln_id) AS application_count,
                AVG(a.docdb_family_size) AS avg_family_size,
                AVG(a.nb_citing_docdb_fam) AS avg_citations
            FROM tls230_appln_techn_field atf
            JOIN tls901_techn_field_ipc tf ON atf.techn_field_nr = tf.techn_field_nr
            JOIN tls201_appln a ON atf.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN 2018 AND 2022
              AND atf.weight > 0.5
            GROUP BY tf.techn_field, tf.techn_sector
            ORDER BY application_count DESC
            LIMIT 15
        """,
        "sql_template": """
            SELECT
                tf.techn_field,
                tf.techn_sector,
                COUNT(DISTINCT a.appln_id) AS application_count,
                ROUND(AVG(a.docdb_family_size), 2) AS avg_family_size,
                ROUND(AVG(a.nb_citing_docdb_fam), 2) AS avg_citations
            FROM tls230_appln_techn_field atf
            JOIN tls901_techn_field_ipc tf ON atf.techn_field_nr = tf.techn_field_nr
            JOIN tls201_appln a ON atf.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
              AND atf.weight > 0.5
              AND a.appln_auth IN UNNEST(@jurisdictions)
              AND (@tech_sector = 'All Sectors' OR tf.techn_sector = @tech_sector)
            GROUP BY tf.techn_field, tf.techn_sector
            ORDER BY application_count DESC
            LIMIT 15
        """
    },

    "Q09": {
        "title": "Who leads in AI-based ERP patents?",
        "tags": ["BUSINESS"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "AI-based enterprise resource planning (G06Q10 + G06N) landscape",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """This query analyzes the patent landscape for AI-based ERP by identifying
applications with both G06Q10 (ERP/business methods) and G06N (AI/machine learning)
CPC classifications.

G06Q 10/ = ERP/administration/management
G06N = AI/Machine Learning

Identifies top applicants to monitor in this emerging technology intersection.""",
        "key_outputs": [
            "Top 10 applicants in AI+ERP space",
            "Patent counts per applicant",
            "Active years (innovation consistency)",
            "First and latest filing dates"
        ],
        "estimated_seconds_first_run": 4,
        "estimated_seconds_cached": 1,
        "visualization": {
            "x": "person_name",
            "y": "patent_count",
            "type": "bar"
        },
        "sql": """
            WITH ai_erp_patents AS (
                SELECT DISTINCT
                    a.appln_id,
                    a.appln_filing_date,
                    a.appln_filing_year
                FROM tls201_appln a
                WHERE a.appln_filing_year >= 2018
                  AND EXISTS (
                    SELECT 1 FROM tls224_appln_cpc cpc1
                    WHERE cpc1.appln_id = a.appln_id
                      AND cpc1.cpc_class_symbol LIKE 'G06Q%'
                      AND cpc1.cpc_class_symbol LIKE '%10/%'
                  )
                  AND EXISTS (
                    SELECT 1 FROM tls224_appln_cpc cpc2
                    WHERE cpc2.appln_id = a.appln_id
                      AND cpc2.cpc_class_symbol LIKE 'G06N%'
                  )
            ),
            top_applicants AS (
                SELECT
                    p.person_id,
                    p.person_name,
                    p.person_ctry_code,
                    p.psn_sector,
                    COUNT(DISTINCT aep.appln_id) AS patent_count,
                    MIN(aep.appln_filing_date) AS first_filing_date,
                    MAX(aep.appln_filing_date) AS latest_filing_date,
                    COUNT(DISTINCT aep.appln_filing_year) AS active_years
                FROM ai_erp_patents aep
                JOIN tls207_pers_appln pa ON aep.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE pa.applt_seq_nr > 0
                GROUP BY p.person_id, p.person_name, p.person_ctry_code, p.psn_sector
                ORDER BY patent_count DESC
                LIMIT 10
            )
            SELECT
                person_name,
                person_ctry_code AS country,
                psn_sector AS sector,
                patent_count,
                active_years,
                CAST(first_filing_date AS STRING) AS first_filing,
                CAST(latest_filing_date AS STRING) AS latest_filing
            FROM top_applicants
            ORDER BY patent_count DESC
        """,
        "sql_template": """
            WITH ai_erp_patents AS (
                SELECT DISTINCT
                    a.appln_id,
                    a.appln_filing_date,
                    a.appln_filing_year
                FROM tls201_appln a
                WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND a.appln_auth IN UNNEST(@jurisdictions)
                  AND EXISTS (
                    SELECT 1 FROM tls224_appln_cpc cpc1
                    WHERE cpc1.appln_id = a.appln_id
                      AND cpc1.cpc_class_symbol LIKE 'G06Q%'
                      AND cpc1.cpc_class_symbol LIKE '%10/%'
                  )
                  AND EXISTS (
                    SELECT 1 FROM tls224_appln_cpc cpc2
                    WHERE cpc2.appln_id = a.appln_id
                      AND cpc2.cpc_class_symbol LIKE 'G06N%'
                  )
            ),
            top_applicants AS (
                SELECT
                    p.person_id,
                    p.person_name,
                    p.person_ctry_code,
                    p.psn_sector,
                    COUNT(DISTINCT aep.appln_id) AS patent_count,
                    MIN(aep.appln_filing_date) AS first_filing_date,
                    MAX(aep.appln_filing_date) AS latest_filing_date,
                    COUNT(DISTINCT aep.appln_filing_year) AS active_years
                FROM ai_erp_patents aep
                JOIN tls207_pers_appln pa ON aep.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE pa.applt_seq_nr > 0
                GROUP BY p.person_id, p.person_name, p.person_ctry_code, p.psn_sector
                ORDER BY patent_count DESC
                LIMIT 10
            )
            SELECT
                person_name,
                person_ctry_code AS country,
                psn_sector AS sector,
                patent_count,
                active_years,
                CAST(first_filing_date AS STRING) AS first_filing,
                CAST(latest_filing_date AS STRING) AS latest_filing
            FROM top_applicants
            ORDER BY patent_count DESC
        """
    },

    "Q10": {
        "title": "Who is building AI-assisted diagnostics portfolios?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Companies building patent portfolios in AI-assisted diagnostics (A61B + G06N)",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """This query identifies companies active in AI-assisted diagnostics by finding
patents at the intersection of medical diagnosis (A61B) and artificial
intelligence (G06N) classifications. It calculates time-to-grant using the
first grant publication date.

Focuses on granted patents from companies (psn_sector = 'COMPANY') to show
established players in this field.""",
        "key_outputs": [
            "Companies ranked by AI diagnostics patent portfolio size",
            "Average time-to-grant in days and years",
            "Focus on granted patents only"
        ],
        "estimated_seconds_first_run": 25,
        "estimated_seconds_cached": 9,
        "visualization": {
            "x": "company_name",
            "y": "patent_count",
            "type": "bar"
        },
        "sql": """
            WITH ai_diagnostics_patents AS (
                SELECT DISTINCT
                    a61b.appln_id,
                    app.appln_filing_date,
                    app.granted,
                    app.earliest_filing_date
                FROM tls209_appln_ipc a61b
                JOIN tls209_appln_ipc g06n ON a61b.appln_id = g06n.appln_id
                JOIN tls201_appln app ON a61b.appln_id = app.appln_id
                WHERE a61b.ipc_class_symbol LIKE 'A61B%'
                  AND g06n.ipc_class_symbol LIKE 'G06N%'
                  AND app.granted = 'Y'
            ),
            granted_patents_with_publn AS (
                SELECT
                    adp.appln_id,
                    adp.appln_filing_date,
                    adp.earliest_filing_date,
                    pub.publn_date AS grant_date
                FROM ai_diagnostics_patents adp
                JOIN tls211_pat_publn pub ON adp.appln_id = pub.appln_id
                WHERE pub.publn_first_grant = 'Y'
                  AND pub.publn_date IS NOT NULL
            ),
            company_patents AS (
                SELECT
                    gpe.appln_id,
                    gpe.appln_filing_date,
                    gpe.grant_date,
                    p.person_id,
                    p.person_name,
                    p.psn_sector
                FROM granted_patents_with_publn gpe
                JOIN tls207_pers_appln pa ON gpe.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE pa.applt_seq_nr > 0
                  AND p.psn_sector = 'COMPANY'
            ),
            time_to_grant_calc AS (
                SELECT
                    person_id,
                    person_name,
                    appln_id,
                    appln_filing_date,
                    grant_date,
                    DATE_DIFF(grant_date, appln_filing_date, DAY) AS days_to_grant
                FROM company_patents
                WHERE grant_date IS NOT NULL
                  AND appln_filing_date IS NOT NULL
                  AND grant_date >= appln_filing_date
            )
            SELECT
                person_name AS company_name,
                COUNT(DISTINCT appln_id) AS patent_count,
                ROUND(AVG(days_to_grant), 0) AS avg_days_to_grant,
                ROUND(AVG(days_to_grant) / 365.25, 1) AS avg_years_to_grant
            FROM time_to_grant_calc
            GROUP BY person_id, person_name
            HAVING COUNT(DISTINCT appln_id) >= 2
            ORDER BY patent_count DESC, avg_days_to_grant ASC
        """,
        "sql_template": """
            WITH ai_diagnostics_patents AS (
                SELECT DISTINCT
                    a61b.appln_id,
                    app.appln_filing_date,
                    app.granted,
                    app.earliest_filing_date
                FROM tls209_appln_ipc a61b
                JOIN tls209_appln_ipc g06n ON a61b.appln_id = g06n.appln_id
                JOIN tls201_appln app ON a61b.appln_id = app.appln_id
                WHERE a61b.ipc_class_symbol LIKE 'A61B%'
                  AND g06n.ipc_class_symbol LIKE 'G06N%'
                  AND app.granted = 'Y'
                  AND app.appln_filing_year BETWEEN @year_start AND @year_end
                  AND app.appln_auth IN UNNEST(@jurisdictions)
            ),
            granted_patents_with_publn AS (
                SELECT
                    adp.appln_id,
                    adp.appln_filing_date,
                    adp.earliest_filing_date,
                    pub.publn_date AS grant_date
                FROM ai_diagnostics_patents adp
                JOIN tls211_pat_publn pub ON adp.appln_id = pub.appln_id
                WHERE pub.publn_first_grant = 'Y'
                  AND pub.publn_date IS NOT NULL
            ),
            company_patents AS (
                SELECT
                    gpe.appln_id,
                    gpe.appln_filing_date,
                    gpe.grant_date,
                    p.person_id,
                    p.person_name,
                    p.psn_sector
                FROM granted_patents_with_publn gpe
                JOIN tls207_pers_appln pa ON gpe.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE pa.applt_seq_nr > 0
                  AND p.psn_sector = 'COMPANY'
            ),
            time_to_grant_calc AS (
                SELECT
                    person_id,
                    person_name,
                    appln_id,
                    appln_filing_date,
                    grant_date,
                    DATE_DIFF(grant_date, appln_filing_date, DAY) AS days_to_grant
                FROM company_patents
                WHERE grant_date IS NOT NULL
                  AND appln_filing_date IS NOT NULL
                  AND grant_date >= appln_filing_date
            )
            SELECT
                person_name AS company_name,
                COUNT(DISTINCT appln_id) AS patent_count,
                ROUND(AVG(days_to_grant), 0) AS avg_days_to_grant,
                ROUND(AVG(days_to_grant) / 365.25, 1) AS avg_years_to_grant
            FROM time_to_grant_calc
            GROUP BY person_id, person_name
            HAVING COUNT(DISTINCT appln_id) >= 2
            ORDER BY patent_count DESC, avg_days_to_grant ASC
        """
    },

    # =========================================================================
    # COMPETITIVE INTELLIGENCE (Q11-Q12)
    # =========================================================================
    "Q11": {
        "title": "Who are the top patent applicants?",
        "tags": ["BUSINESS"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Top patent applicants with portfolio profile",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            },
            "applicant_name": {
                "type": "text",
                "label": "Applicant Name Filter",
                "defaults": "",
                "placeholder": "e.g., Samsung, Siemens (leave empty for all)",
                "required": False
            }
        },
        "explanation": """This query identifies the most prolific patent applicants by standardized
name (doc_std_name), showing their filing activity, grant success, and
temporal span of innovation. The unique_patent_families count helps
distinguish genuine innovation from defensive filing strategies.

Minimum threshold of 50 patents ensures focus on significant players.""",
        "key_outputs": [
            "Top applicants ranked by volume",
            "Grant success rate per applicant",
            "Innovation timeline (first to last filing)",
            "Unique patent families (true innovation count)"
        ],
        "estimated_seconds_first_run": 12,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                p.doc_std_name,
                p.person_ctry_code,
                COUNT(DISTINCT a.appln_id) AS total_applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted_patents,
                MIN(a.appln_filing_year) AS first_filing_year,
                MAX(a.appln_filing_year) AS last_filing_year,
                COUNT(DISTINCT a.docdb_family_id) AS unique_patent_families
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND p.doc_std_name IS NOT NULL
              AND a.appln_filing_year >= 2010
            GROUP BY p.doc_std_name, p.person_ctry_code
            HAVING COUNT(DISTINCT a.appln_id) >= 50
            ORDER BY total_applications DESC
            LIMIT 25
        """,
        "sql_template": """
            SELECT
                p.doc_std_name,
                p.person_ctry_code,
                COUNT(DISTINCT a.appln_id) AS total_applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted_patents,
                MIN(a.appln_filing_year) AS first_filing_year,
                MAX(a.appln_filing_year) AS last_filing_year,
                COUNT(DISTINCT a.docdb_family_id) AS unique_patent_families
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND p.doc_std_name IS NOT NULL
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND a.appln_auth IN UNNEST(@jurisdictions)
              AND (@applicant_name = '' OR LOWER(p.doc_std_name) LIKE CONCAT('%', LOWER(@applicant_name), '%'))
            GROUP BY p.doc_std_name, p.person_ctry_code
            HAVING COUNT(DISTINCT a.appln_id) >= CASE WHEN @applicant_name = '' THEN 50 ELSE 1 END
            ORDER BY total_applications DESC
            LIMIT 25
        """
    },

    "Q12": {
        "title": "Where do MedTech competitors file their patents?",
        "tags": ["BUSINESS"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Geographic filing patterns of major MedTech competitors",
        "visualization": None,
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices to Compare",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            },
            "competitors": {
                "type": "multiselect",
                "label": "Competitors to Analyze",
                "options": "medtech_competitors",
                "defaults": ["Medtronic", "Johnson & Johnson", "Abbott", "Boston Scientific", "Stryker"],
                "required": True
            }
        },
        "explanation": """This query analyzes the geographic filing patterns of major MedTech competitors,
focusing on EP (European Patent Office), US (USPTO), and CN (CNIPA) filings.

Uses WIPO technology sector classification (Instruments) instead of direct IPC patterns.
Competitor list includes: Medtronic, Johnson & Johnson, Abbott, Boston Scientific,
Stryker, Zimmer, Smith & Nephew, Edwards, Baxter, Fresenius, and B. Braun.""",
        "key_outputs": [
            "Filing distribution by patent office (EP/US/CN)",
            "Percentage breakdown per competitor",
            "Patent counts per authority"
        ],
        "estimated_seconds_first_run": 4,
        "estimated_seconds_cached": 1,
        "sql": """
            WITH medical_tech_applications AS (
                SELECT DISTINCT
                    a.appln_id,
                    a.appln_auth,
                    a.appln_filing_date,
                    p.person_name AS applicant_name,
                    p.person_id
                FROM tls201_appln a
                JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                JOIN tls230_appln_techn_field tf ON a.appln_id = tf.appln_id
                JOIN tls901_techn_field_ipc tfi ON tf.techn_field_nr = tfi.techn_field_nr
                WHERE pa.applt_seq_nr > 0
                  AND tfi.techn_sector = 'Instruments'
                  AND a.appln_filing_year >= 2010
                  AND (
                    LOWER(p.person_name) LIKE '%medtronic%' OR
                    LOWER(p.person_name) LIKE '%johnson%johnson%' OR
                    LOWER(p.person_name) LIKE '%abbott%' OR
                    LOWER(p.person_name) LIKE '%boston%scientific%' OR
                    LOWER(p.person_name) LIKE '%stryker%' OR
                    LOWER(p.person_name) LIKE '%zimmer%' OR
                    LOWER(p.person_name) LIKE '%smith%nephew%' OR
                    LOWER(p.person_name) LIKE '%edwards%' OR
                    LOWER(p.person_name) LIKE '%baxter%' OR
                    LOWER(p.person_name) LIKE '%fresenius%' OR
                    LOWER(p.person_name) LIKE '%braun%'
                  )
            )
            SELECT
                mta.applicant_name,
                mta.appln_auth AS filing_authority,
                COUNT(*) AS patent_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY mta.applicant_name), 2) AS percentage_by_applicant,
                CASE
                    WHEN mta.appln_auth = 'EP' THEN 'European Patent Office'
                    WHEN mta.appln_auth = 'US' THEN 'United States Patent Office'
                    WHEN mta.appln_auth = 'CN' THEN 'China Patent Office'
                    ELSE 'Other Authority'
                END AS authority_description
            FROM medical_tech_applications mta
            WHERE mta.appln_auth IN ('EP', 'US', 'CN')
            GROUP BY mta.applicant_name, mta.appln_auth
            HAVING COUNT(*) >= 10
            ORDER BY mta.applicant_name, patent_count DESC
        """,
        "sql_template": """
            WITH competitor_patterns AS (
                SELECT LOWER(competitor) AS pattern
                FROM UNNEST(@competitors) AS competitor
            ),
            medical_tech_applications AS (
                SELECT DISTINCT
                    a.appln_id,
                    a.appln_auth,
                    a.appln_filing_date,
                    p.person_name AS applicant_name,
                    p.person_id
                FROM tls201_appln a
                JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                JOIN tls230_appln_techn_field tf ON a.appln_id = tf.appln_id
                JOIN tls901_techn_field_ipc tfi ON tf.techn_field_nr = tfi.techn_field_nr
                WHERE pa.applt_seq_nr > 0
                  AND tfi.techn_sector = 'Instruments'
                  AND a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND EXISTS (
                    SELECT 1 FROM competitor_patterns cp
                    WHERE LOWER(p.person_name) LIKE CONCAT('%', cp.pattern, '%')
                  )
            )
            SELECT
                mta.applicant_name,
                mta.appln_auth AS filing_authority,
                COUNT(*) AS patent_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY mta.applicant_name), 2) AS percentage_by_applicant,
                CASE
                    WHEN mta.appln_auth = 'EP' THEN 'European Patent Office'
                    WHEN mta.appln_auth = 'US' THEN 'United States Patent Office'
                    WHEN mta.appln_auth = 'CN' THEN 'China Patent Office'
                    ELSE 'Other Authority'
                END AS authority_description
            FROM medical_tech_applications mta
            WHERE mta.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY mta.applicant_name, mta.appln_auth
            HAVING COUNT(*) >= 10
            ORDER BY mta.applicant_name, patent_count DESC
        """
    },

    # =========================================================================
    # CITATION & PROSECUTION (Q13-Q14)
    # =========================================================================
    "Q13": {
        "title": "Which patents are most frequently cited?",
        "tags": ["UNIVERSITY"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Most frequently cited patents by recent applications",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Citing Application Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """This query builds a citation network to identify the most influential prior
art patents. By focusing on recent citing applications, it shows which older
patents remain technically relevant. The citation lag metric reveals how
quickly innovations become foundational knowledge in the field.

Minimum threshold of 10 citations ensures significance.""",
        "key_outputs": [
            "Most cited patents (influence indicator)",
            "Citation lag in years (knowledge diffusion speed)",
            "Cited patent filing year"
        ],
        "estimated_seconds_first_run": 22,
        "estimated_seconds_cached": 3,
        "sql": """
            WITH citation_network AS (
                SELECT
                    c.pat_publn_id,
                    c.cited_pat_publn_id,
                    a1.appln_id AS citing_appln_id,
                    a2.appln_id AS cited_appln_id,
                    a1.appln_filing_year AS citing_year,
                    a2.appln_filing_year AS cited_year
                FROM tls212_citation c
                JOIN tls211_pat_publn pp1 ON c.pat_publn_id = pp1.pat_publn_id
                JOIN tls211_pat_publn pp2 ON c.cited_pat_publn_id = pp2.pat_publn_id
                JOIN tls201_appln a1 ON pp1.appln_id = a1.appln_id
                JOIN tls201_appln a2 ON pp2.appln_id = a2.appln_id
                WHERE c.cited_pat_publn_id > 0
                  AND a1.appln_filing_year = 2020
            )
            SELECT
                cited_appln_id,
                cited_year,
                COUNT(DISTINCT citing_appln_id) AS times_cited_in_2020,
                AVG(citing_year - cited_year) AS avg_citation_lag_years
            FROM citation_network
            GROUP BY cited_appln_id, cited_year
            HAVING COUNT(DISTINCT citing_appln_id) >= 10
            ORDER BY times_cited_in_2020 DESC
            LIMIT 20
        """,
        "sql_template": """
            WITH citation_network AS (
                SELECT
                    c.pat_publn_id,
                    c.cited_pat_publn_id,
                    a1.appln_id AS citing_appln_id,
                    a2.appln_id AS cited_appln_id,
                    a1.appln_filing_year AS citing_year,
                    a2.appln_filing_year AS cited_year
                FROM tls212_citation c
                JOIN tls211_pat_publn pp1 ON c.pat_publn_id = pp1.pat_publn_id
                JOIN tls211_pat_publn pp2 ON c.cited_pat_publn_id = pp2.pat_publn_id
                JOIN tls201_appln a1 ON pp1.appln_id = a1.appln_id
                JOIN tls201_appln a2 ON pp2.appln_id = a2.appln_id
                WHERE c.cited_pat_publn_id > 0
                  AND a1.appln_filing_year BETWEEN @year_start AND @year_end
                  AND a1.appln_auth IN UNNEST(@jurisdictions)
            )
            SELECT
                cited_appln_id,
                cited_year,
                COUNT(DISTINCT citing_appln_id) AS times_cited,
                ROUND(AVG(citing_year - cited_year), 1) AS avg_citation_lag_years
            FROM citation_network
            GROUP BY cited_appln_id, cited_year
            HAVING COUNT(DISTINCT citing_appln_id) >= 10
            ORDER BY times_cited DESC
            LIMIT 20
        """
    },

    "Q14": {
        "title": "What are grant rates for diagnostic imaging patents?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Grant rates for diagnostic imaging patents (A61B 6/) by patent office",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            },
            "ipc_class": {
                "type": "text",
                "label": "IPC Class",
                "defaults": "A61B 6",
                "placeholder": "e.g., A61B 6, G06N, H01L",
                "required": True
            }
        },
        "explanation": """This query analyzes grant rates for diagnostic imaging patents (IPC subclass A61B 6/)
across major patent offices. A61B 6/ covers diagnostic imaging technologies
including X-ray, ultrasound, MRI, and other medical imaging devices.

Uses combined LIKE patterns to handle variable whitespace in IPC codes.
Helps inform international filing strategy by showing office-specific grant success.""",
        "key_outputs": [
            "Grant rates by patent office",
            "Total applications vs. granted patents",
            "Office comparison for filing strategy"
        ],
        "estimated_seconds_first_run": 2,
        "estimated_seconds_cached": 1,
        "sql": """
            WITH diagnostic_imaging_patents AS (
                SELECT DISTINCT
                    a.appln_id,
                    a.appln_auth,
                    a.granted
                FROM tls201_appln a
                JOIN tls209_appln_ipc ipc ON a.appln_id = ipc.appln_id
                WHERE ipc.ipc_class_symbol LIKE 'A61B%'
                  AND ipc.ipc_class_symbol LIKE '%6/%'
                  AND ipc.ipc_class_symbol NOT LIKE '%16/%'
                  AND ipc.ipc_class_symbol NOT LIKE '%26/%'
                  AND ipc.ipc_class_symbol NOT LIKE '%36/%'
                  AND ipc.ipc_class_symbol NOT LIKE '%46/%'
                  AND ipc.ipc_class_symbol NOT LIKE '%56/%'
                  AND a.appln_auth IN ('EP', 'US', 'CN')
                  AND a.appln_filing_year BETWEEN 2010 AND 2023
            )
            SELECT
                CASE
                    WHEN appln_auth = 'EP' THEN 'European Patent Office (EPO)'
                    WHEN appln_auth = 'US' THEN 'USPTO'
                    WHEN appln_auth = 'CN' THEN 'CNIPA'
                END AS office_name,
                appln_auth AS office_code,
                COUNT(*) AS total_applications,
                COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted_patents,
                ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS grant_rate_pct
            FROM diagnostic_imaging_patents
            GROUP BY appln_auth
            ORDER BY grant_rate_pct DESC
        """,
        "sql_template": """
            WITH technology_patents AS (
                SELECT DISTINCT
                    a.appln_id,
                    a.appln_auth,
                    a.granted
                FROM tls201_appln a
                JOIN tls209_appln_ipc ipc ON a.appln_id = ipc.appln_id
                WHERE ipc.ipc_class_symbol LIKE CONCAT(REPLACE(@ipc_class, ' ', ''), '%')
                  AND a.appln_auth IN UNNEST(@jurisdictions)
                  AND a.appln_filing_year BETWEEN @year_start AND @year_end
            )
            SELECT
                CASE
                    WHEN appln_auth = 'EP' THEN 'European Patent Office (EPO)'
                    WHEN appln_auth = 'US' THEN 'USPTO'
                    WHEN appln_auth = 'CN' THEN 'CNIPA'
                    ELSE appln_auth
                END AS office_name,
                appln_auth AS office_code,
                COUNT(*) AS total_applications,
                COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted_patents,
                ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS grant_rate_pct
            FROM technology_patents
            GROUP BY appln_auth
            ORDER BY grant_rate_pct DESC
        """
    },

    # =========================================================================
    # REGIONAL ANALYSIS - GERMANY (Q15-Q17)
    # =========================================================================
    "Q15": {
        "title": "Which German states lead in medical tech patents?",
        "tags": ["PATLIB"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "German Federal states patent activity in A61B (Diagnosis/Surgery)",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "ipc_class": {
                "type": "text",
                "label": "IPC Main Class",
                "defaults": "A61B",
                "placeholder": "e.g., A61B, G06F, H01L",
                "required": True
            }
        },
        "explanation": """This query provides analysis of medical technology patent activity
across German federal states using NUTS codes. It identifies regional
innovation hubs in the medical diagnosis/surgery field (IPC A61B) and
calculates grant rates as a quality indicator.

Uses main class A61B% - covers all medical diagnosis/surgery subclasses.""",
        "key_outputs": [
            "Federal states ranked by patent activity",
            "Grant rates per region",
            "Unique applicants and patent families"
        ],
        "estimated_seconds_first_run": 4,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                n.nuts AS bundesland_code,
                n.nuts_label AS bundesland,
                COUNT(DISTINCT a.appln_id) AS total_applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted_patents,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct,
                COUNT(DISTINCT p.person_id) AS unique_applicants,
                COUNT(DISTINCT a.docdb_family_id) AS unique_families
            FROM tls201_appln a
            JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls209_appln_ipc ipc ON a.appln_id = ipc.appln_id
            JOIN tls904_nuts n ON SUBSTR(p.nuts, 1, 3) = n.nuts AND n.nuts_level = 1
            WHERE a.appln_filing_year BETWEEN 2018 AND 2023
              AND pa.applt_seq_nr > 0
              AND p.person_ctry_code = 'DE'
              AND p.nuts_level >= 1
              AND ipc.ipc_class_symbol LIKE 'A61B%'
            GROUP BY n.nuts, n.nuts_label
            HAVING COUNT(DISTINCT a.appln_id) >= 10
            ORDER BY total_applications DESC
        """,
        "sql_template": """
            SELECT
                n.nuts AS bundesland_code,
                n.nuts_label AS bundesland,
                COUNT(DISTINCT a.appln_id) AS total_applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted_patents,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct,
                COUNT(DISTINCT p.person_id) AS unique_applicants,
                COUNT(DISTINCT a.docdb_family_id) AS unique_families
            FROM tls201_appln a
            JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls209_appln_ipc ipc ON a.appln_id = ipc.appln_id
            JOIN tls904_nuts n ON SUBSTR(p.nuts, 1, 3) = n.nuts AND n.nuts_level = 1
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
              AND pa.applt_seq_nr > 0
              AND p.person_ctry_code = 'DE'
              AND p.nuts_level >= 1
              AND ipc.ipc_class_symbol LIKE CONCAT(REPLACE(@ipc_class, ' ', ''), '%')
            GROUP BY n.nuts, n.nuts_label
            HAVING COUNT(DISTINCT a.appln_id) >= 10
            ORDER BY total_applications DESC
        """
    },

    "Q16": {
        "title": "How do German states compare per capita in medical tech?",
        "tags": ["PATLIB"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "A61B patent activity by German federal state with per-capita comparison",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "ipc_class": {
                "type": "text",
                "label": "IPC Main Class",
                "defaults": "A61B",
                "placeholder": "e.g., A61B, G06F, H01L",
                "required": True
            }
        },
        "explanation": """This query analyzes patent activity in IPC class A61B (medical diagnosis/surgery)
focusing on German federal states with per-capita comparison.

Population data from Statistisches Bundesamt (destatis.de), Stand 31.12.2023.
Normalizes patent counts by population to enable fair comparison between
states of different sizes.""",
        "key_outputs": [
            "German federal states ranked by patent count",
            "Patents per million inhabitants (normalized comparison)",
            "Percentage of total German patents",
            "Rank by total vs. rank per capita"
        ],
        "estimated_seconds_first_run": 6,
        "estimated_seconds_cached": 1,
        "sql": """
            WITH population_2023 AS (
                SELECT * FROM UNNEST([
                    STRUCT('DE1' AS nuts_code, 'BADEN-WÜRTTEMBERG' AS bundesland, 11280000 AS population),
                    STRUCT('DE2', 'BAYERN', 13370000),
                    STRUCT('DE3', 'BERLIN', 3850000),
                    STRUCT('DE4', 'BRANDENBURG', 2570000),
                    STRUCT('DE5', 'BREMEN', 680000),
                    STRUCT('DE6', 'HAMBURG', 1950000),
                    STRUCT('DE7', 'HESSEN', 6390000),
                    STRUCT('DE8', 'MECKLENBURG-VORPOMMERN', 1610000),
                    STRUCT('DE9', 'NIEDERSACHSEN', 8140000),
                    STRUCT('DEA', 'NORDRHEIN-WESTFALEN', 18140000),
                    STRUCT('DEB', 'RHEINLAND-PFALZ', 4160000),
                    STRUCT('DEC', 'SAARLAND', 990000),
                    STRUCT('DED', 'SACHSEN', 4090000),
                    STRUCT('DEE', 'SACHSEN-ANHALT', 2170000),
                    STRUCT('DEF', 'SCHLESWIG-HOLSTEIN', 2950000),
                    STRUCT('DEG', 'THÜRINGEN', 2110000)
                ])
            ),
            recent_patents AS (
                SELECT
                    a.appln_id,
                    p.person_id,
                    p.nuts
                FROM tls201_appln a
                JOIN tls209_appln_ipc ipc ON a.appln_id = ipc.appln_id
                JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE ipc.ipc_class_symbol LIKE 'A61B%'
                  AND a.appln_filing_year >= 2019
                  AND pa.applt_seq_nr > 0
                  AND p.person_ctry_code = 'DE'
                  AND p.nuts_level >= 1
            ),
            german_state_activity AS (
                SELECT
                    SUBSTR(rp.nuts, 1, 3) AS nuts_code,
                    COUNT(DISTINCT rp.appln_id) AS patent_count,
                    COUNT(DISTINCT rp.person_id) AS applicant_count
                FROM recent_patents rp
                GROUP BY SUBSTR(rp.nuts, 1, 3)
            )
            SELECT
                RANK() OVER (ORDER BY gsa.patent_count DESC) AS rank_total,
                pop.nuts_code,
                pop.bundesland,
                gsa.patent_count,
                gsa.applicant_count,
                ROUND(pop.population / 1000000.0, 2) AS population_mio,
                ROUND(gsa.patent_count * 1000000.0 / pop.population, 1) AS patents_per_mio_inhabitants,
                RANK() OVER (ORDER BY gsa.patent_count * 1.0 / pop.population DESC) AS rank_per_capita,
                ROUND(gsa.patent_count * 100.0 / SUM(gsa.patent_count) OVER (), 1) AS pct_of_total
            FROM german_state_activity gsa
            JOIN population_2023 pop ON gsa.nuts_code = pop.nuts_code
            ORDER BY patents_per_mio_inhabitants DESC
        """,
        "sql_template": """
            WITH population_2023 AS (
                SELECT * FROM UNNEST([
                    STRUCT('DE1' AS nuts_code, 'BADEN-WÜRTTEMBERG' AS bundesland, 11280000 AS population),
                    STRUCT('DE2', 'BAYERN', 13370000),
                    STRUCT('DE3', 'BERLIN', 3850000),
                    STRUCT('DE4', 'BRANDENBURG', 2570000),
                    STRUCT('DE5', 'BREMEN', 680000),
                    STRUCT('DE6', 'HAMBURG', 1950000),
                    STRUCT('DE7', 'HESSEN', 6390000),
                    STRUCT('DE8', 'MECKLENBURG-VORPOMMERN', 1610000),
                    STRUCT('DE9', 'NIEDERSACHSEN', 8140000),
                    STRUCT('DEA', 'NORDRHEIN-WESTFALEN', 18140000),
                    STRUCT('DEB', 'RHEINLAND-PFALZ', 4160000),
                    STRUCT('DEC', 'SAARLAND', 990000),
                    STRUCT('DED', 'SACHSEN', 4090000),
                    STRUCT('DEE', 'SACHSEN-ANHALT', 2170000),
                    STRUCT('DEF', 'SCHLESWIG-HOLSTEIN', 2950000),
                    STRUCT('DEG', 'THÜRINGEN', 2110000)
                ])
            ),
            recent_patents AS (
                SELECT
                    a.appln_id,
                    p.person_id,
                    p.nuts
                FROM tls201_appln a
                JOIN tls209_appln_ipc ipc ON a.appln_id = ipc.appln_id
                JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE ipc.ipc_class_symbol LIKE CONCAT(REPLACE(@ipc_class, ' ', ''), '%')
                  AND a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND pa.applt_seq_nr > 0
                  AND p.person_ctry_code = 'DE'
                  AND p.nuts_level >= 1
            ),
            german_state_activity AS (
                SELECT
                    SUBSTR(rp.nuts, 1, 3) AS nuts_code,
                    COUNT(DISTINCT rp.appln_id) AS patent_count,
                    COUNT(DISTINCT rp.person_id) AS applicant_count
                FROM recent_patents rp
                GROUP BY SUBSTR(rp.nuts, 1, 3)
            )
            SELECT
                RANK() OVER (ORDER BY gsa.patent_count DESC) AS rank_total,
                pop.nuts_code,
                pop.bundesland,
                gsa.patent_count,
                gsa.applicant_count,
                ROUND(pop.population / 1000000.0, 2) AS population_mio,
                ROUND(gsa.patent_count * 1000000.0 / pop.population, 1) AS patents_per_mio_inhabitants,
                RANK() OVER (ORDER BY gsa.patent_count * 1.0 / pop.population DESC) AS rank_per_capita,
                ROUND(gsa.patent_count * 100.0 / SUM(gsa.patent_count) OVER (), 1) AS pct_of_total
            FROM german_state_activity gsa
            JOIN population_2023 pop ON gsa.nuts_code = pop.nuts_code
            ORDER BY patents_per_mio_inhabitants DESC
        """
    },

    "Q17": {
        "title": "How do German regions compare by technology sector?",
        "tags": ["PATLIB"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "Compare German regions patent activity by WIPO technology sectors",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            }
        },
        "explanation": """This query compares patent activity across German federal states (Sachsen, Bayern,
Baden-Württemberg) broken down by WIPO technology sectors. It helps regional
development agencies understand their innovation strengths relative to peer regions.

Uses WIPO technology sector classification via tls901 - provides standardized
technology categorization across all patents.""",
        "key_outputs": [
            "Patent counts by region and technology sector",
            "Recent activity (2018+) highlighted separately",
            "Technology relevance weights for accuracy",
            "Temporal span of innovation activity"
        ],
        "estimated_seconds_first_run": 3,
        "estimated_seconds_cached": 1,
        "visualization": {
            "x": "region_group",
            "y": "patent_count",
            "color": "techn_sector",
            "type": "bar"
        },
        "sql": """
            WITH regional_patents AS (
                SELECT
                    a.appln_id,
                    a.appln_filing_year,
                    p.nuts,
                    CASE
                        WHEN p.nuts LIKE 'DED%' THEN 'Sachsen'
                        WHEN p.nuts LIKE 'DE2%' THEN 'Bayern'
                        WHEN p.nuts LIKE 'DE1%' THEN 'Baden-Württemberg'
                    END AS region_group
                FROM tls201_appln a
                JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE pa.applt_seq_nr > 0
                  AND a.appln_filing_year >= 2010
                  AND p.nuts IS NOT NULL
                  AND (p.nuts LIKE 'DED%' OR p.nuts LIKE 'DE2%' OR p.nuts LIKE 'DE1%')
            ),
            technology_sectors AS (
                SELECT
                    rp.appln_id,
                    rp.region_group,
                    rp.appln_filing_year,
                    tf.techn_sector,
                    tf.techn_field,
                    atf.weight
                FROM regional_patents rp
                JOIN tls230_appln_techn_field atf ON rp.appln_id = atf.appln_id
                JOIN tls901_techn_field_ipc tf ON atf.techn_field_nr = tf.techn_field_nr
            )
            SELECT
                region_group,
                techn_sector,
                COUNT(DISTINCT appln_id) AS patent_count,
                COUNT(DISTINCT CASE WHEN appln_filing_year >= 2018 THEN appln_id END) AS recent_patents_2018_plus,
                ROUND(AVG(weight), 3) AS avg_tech_relevance_weight,
                MIN(appln_filing_year) AS earliest_year,
                MAX(appln_filing_year) AS latest_year
            FROM technology_sectors
            GROUP BY region_group, techn_sector
            ORDER BY region_group, patent_count DESC
        """,
        "sql_template": """
            WITH regional_patents AS (
                SELECT
                    a.appln_id,
                    a.appln_filing_year,
                    p.nuts,
                    CASE
                        WHEN p.nuts LIKE 'DED%' THEN 'Sachsen'
                        WHEN p.nuts LIKE 'DE2%' THEN 'Bayern'
                        WHEN p.nuts LIKE 'DE1%' THEN 'Baden-Württemberg'
                    END AS region_group
                FROM tls201_appln a
                JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE pa.applt_seq_nr > 0
                  AND a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND p.nuts IS NOT NULL
                  AND (p.nuts LIKE 'DED%' OR p.nuts LIKE 'DE2%' OR p.nuts LIKE 'DE1%')
            ),
            technology_sectors AS (
                SELECT
                    rp.appln_id,
                    rp.region_group,
                    rp.appln_filing_year,
                    tf.techn_sector,
                    tf.techn_field,
                    atf.weight
                FROM regional_patents rp
                JOIN tls230_appln_techn_field atf ON rp.appln_id = atf.appln_id
                JOIN tls901_techn_field_ipc tf ON atf.techn_field_nr = tf.techn_field_nr
            )
            SELECT
                region_group,
                techn_sector,
                COUNT(DISTINCT appln_id) AS patent_count,
                COUNT(DISTINCT CASE WHEN appln_filing_year >= @year_start + 3 THEN appln_id END) AS recent_patents,
                ROUND(AVG(weight), 3) AS avg_tech_relevance_weight,
                MIN(appln_filing_year) AS earliest_year,
                MAX(appln_filing_year) AS latest_year
            FROM technology_sectors
            GROUP BY region_group, techn_sector
            ORDER BY region_group, patent_count DESC
        """
    },

    # =========================================================================
    # EPO TRAINING QUERIES - BATCH 1 (Q19-Q28)
    # Extracted and adapted from EPO PATSTAT training materials
    # =========================================================================
    "Q19": {
        "title": "Which applicants have the largest patent families?",
        "tags": ["BUSINESS", "PATLIB"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Applicants with the largest average patent family sizes, indicating global filing strategies",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies applicants whose inventions are protected across the most jurisdictions.
Large family sizes typically indicate:
- High-value inventions worth global protection
- Strong international filing strategies
- Resources to pursue worldwide patent protection

The docdb_family_size counts distinct applications in the same DOCDB family.
Minimum 10 families ensures statistical relevance.""",
        "key_outputs": [
            "Applicant names ranked by avg family size",
            "Number of patent families per applicant",
            "Average and maximum family sizes"
        ],
        "methodology": "Uses DOCDB family grouping from tls201_appln, filtered for recent filings",
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 2,
        "visualization": {
            "x": "applicant_name",
            "y": "avg_family_size",
            "type": "bar"
        },
        "sql": """
            SELECT
                p.doc_std_name AS applicant_name,
                p.person_ctry_code AS country,
                COUNT(DISTINCT a.docdb_family_id) AS patent_families,
                ROUND(AVG(a.docdb_family_size), 1) AS avg_family_size,
                MAX(a.docdb_family_size) AS max_family_size
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND a.appln_filing_year BETWEEN 2018 AND 2023
              AND p.doc_std_name IS NOT NULL
              AND a.docdb_family_size > 1
            GROUP BY p.doc_std_name, p.person_ctry_code
            HAVING COUNT(DISTINCT a.docdb_family_id) >= 10
            ORDER BY avg_family_size DESC
            LIMIT 25
        """,
        "sql_template": """
            SELECT
                p.doc_std_name AS applicant_name,
                p.person_ctry_code AS country,
                COUNT(DISTINCT a.docdb_family_id) AS patent_families,
                ROUND(AVG(a.docdb_family_size), 1) AS avg_family_size,
                MAX(a.docdb_family_size) AS max_family_size
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND p.doc_std_name IS NOT NULL
              AND a.docdb_family_size > 1
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY p.doc_std_name, p.person_ctry_code
            HAVING COUNT(DISTINCT a.docdb_family_id) >= 10
            ORDER BY avg_family_size DESC
            LIMIT 25
        """
    },

    "Q20": {
        "title": "Who are the most prolific inventors?",
        "tags": ["UNIVERSITY", "BUSINESS"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Inventors with the highest number of patent applications",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies the most productive inventors by counting their patent applications.
Prolific inventors often represent key R&D talent at companies or research institutions.

Uses invt_seq_nr > 0 to filter for inventors only (excluding applicants who aren't inventors).
The person_name field contains the inventor's name as filed.""",
        "key_outputs": [
            "Top inventors ranked by application count",
            "Inventor country of residence",
            "Number of distinct patent families"
        ],
        "methodology": "Counts distinct applications per inventor from tls207_pers_appln",
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 2,
        "visualization": {
            "x": "inventor_name",
            "y": "application_count",
            "type": "bar"
        },
        "sql": """
            SELECT
                p.person_name AS inventor_name,
                p.person_ctry_code AS country,
                COUNT(DISTINCT a.appln_id) AS application_count,
                COUNT(DISTINCT a.docdb_family_id) AS family_count,
                MIN(a.appln_filing_year) AS first_filing_year,
                MAX(a.appln_filing_year) AS last_filing_year
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.invt_seq_nr > 0
              AND a.appln_filing_year BETWEEN 2018 AND 2023
              AND p.person_name IS NOT NULL
              AND p.person_ctry_code IS NOT NULL
            GROUP BY p.person_name, p.person_ctry_code
            HAVING COUNT(DISTINCT a.appln_id) >= 20
            ORDER BY application_count DESC
            LIMIT 25
        """,
        "sql_template": """
            SELECT
                p.person_name AS inventor_name,
                p.person_ctry_code AS country,
                COUNT(DISTINCT a.appln_id) AS application_count,
                COUNT(DISTINCT a.docdb_family_id) AS family_count,
                MIN(a.appln_filing_year) AS first_filing_year,
                MAX(a.appln_filing_year) AS last_filing_year
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.invt_seq_nr > 0
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND p.person_name IS NOT NULL
              AND p.person_ctry_code IS NOT NULL
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY p.person_name, p.person_ctry_code
            HAVING COUNT(DISTINCT a.appln_id) >= 20
            ORDER BY application_count DESC
            LIMIT 25
        """
    },

    "Q21": {
        "title": "Which companies collaborate internationally on patents?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Applicants who co-file patents with partners from other countries",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies international collaboration patterns by finding applications
with co-applicants from different countries. This reveals:
- R&D partnerships between companies
- University-industry collaborations across borders
- Joint venture patent activity

Based on EPO training query 2.3 - finding applicants with international co-applicants.""",
        "key_outputs": [
            "Applicant pairs with different country codes",
            "Number of joint applications",
            "Countries involved in collaboration"
        ],
        "methodology": "Self-join on tls207_pers_appln to find co-applicants with different countries",
        "estimated_seconds_first_run": 12,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                p1.doc_std_name AS applicant_1,
                p1.person_ctry_code AS country_1,
                p2.doc_std_name AS applicant_2,
                p2.person_ctry_code AS country_2,
                COUNT(DISTINCT pa1.appln_id) AS joint_applications
            FROM tls207_pers_appln pa1
            JOIN tls206_person p1 ON pa1.person_id = p1.person_id
            JOIN tls207_pers_appln pa2 ON pa1.appln_id = pa2.appln_id
            JOIN tls206_person p2 ON pa2.person_id = p2.person_id
            JOIN tls201_appln a ON pa1.appln_id = a.appln_id
            WHERE pa1.applt_seq_nr > 0
              AND pa2.applt_seq_nr > 0
              AND p1.person_ctry_code <> p2.person_ctry_code
              AND p1.doc_std_name < p2.doc_std_name
              AND a.appln_filing_year BETWEEN 2018 AND 2023
              AND p1.doc_std_name IS NOT NULL
              AND p2.doc_std_name IS NOT NULL
            GROUP BY p1.doc_std_name, p1.person_ctry_code, p2.doc_std_name, p2.person_ctry_code
            HAVING COUNT(DISTINCT pa1.appln_id) >= 5
            ORDER BY joint_applications DESC
            LIMIT 25
        """,
        "sql_template": """
            SELECT
                p1.doc_std_name AS applicant_1,
                p1.person_ctry_code AS country_1,
                p2.doc_std_name AS applicant_2,
                p2.person_ctry_code AS country_2,
                COUNT(DISTINCT pa1.appln_id) AS joint_applications
            FROM tls207_pers_appln pa1
            JOIN tls206_person p1 ON pa1.person_id = p1.person_id
            JOIN tls207_pers_appln pa2 ON pa1.appln_id = pa2.appln_id
            JOIN tls206_person p2 ON pa2.person_id = p2.person_id
            JOIN tls201_appln a ON pa1.appln_id = a.appln_id
            WHERE pa1.applt_seq_nr > 0
              AND pa2.applt_seq_nr > 0
              AND p1.person_ctry_code <> p2.person_ctry_code
              AND p1.doc_std_name < p2.doc_std_name
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND p1.doc_std_name IS NOT NULL
              AND p2.doc_std_name IS NOT NULL
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY p1.doc_std_name, p1.person_ctry_code, p2.doc_std_name, p2.person_ctry_code
            HAVING COUNT(DISTINCT pa1.appln_id) >= 5
            ORDER BY joint_applications DESC
            LIMIT 25
        """
    },

    "Q22": {
        "title": "What are the most cited patent families?",
        "tags": ["UNIVERSITY", "BUSINESS"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Patent families receiving the most citations from other patent families",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies the most influential inventions by counting how many other
patent families cite them. Citation counts at the family level (nb_citing_docdb_fam) are
more meaningful than publication-level counts because they measure true technical influence.

Based on EPO training query 2.1 - most cited applications.""",
        "key_outputs": [
            "Top cited patent families",
            "Citation counts (DOCDB family level)",
            "Filing year and authority",
            "Family size indicator"
        ],
        "methodology": "Uses pre-calculated nb_citing_docdb_fam from tls201_appln",
        "estimated_seconds_first_run": 3,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                a.docdb_family_id,
                a.appln_auth AS filing_authority,
                a.appln_filing_year,
                a.nb_citing_docdb_fam AS citation_count,
                a.docdb_family_size AS family_size,
                a.granted
            FROM tls201_appln a
            WHERE a.nb_citing_docdb_fam > 0
              AND a.appln_filing_year BETWEEN 2010 AND 2020
              AND a.appln_id = a.earliest_filing_id
            ORDER BY a.nb_citing_docdb_fam DESC
            LIMIT 50
        """,
        "sql_template": """
            SELECT
                a.docdb_family_id,
                a.appln_auth AS filing_authority,
                a.appln_filing_year,
                a.nb_citing_docdb_fam AS citation_count,
                a.docdb_family_size AS family_size,
                a.granted
            FROM tls201_appln a
            WHERE a.nb_citing_docdb_fam > 0
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND a.appln_id = a.earliest_filing_id
              AND a.appln_auth IN UNNEST(@jurisdictions)
            ORDER BY a.nb_citing_docdb_fam DESC
            LIMIT 50
        """
    },

    "Q23": {
        "title": "Where do individual inventors file their patents?",
        "tags": ["PATLIB"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "Filing patterns of inventor-applicants (individuals who are both inventor and applicant)",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            }
        },
        "explanation": """Identifies patent filings where the inventor is also the applicant,
typically indicating individual inventors or small entities rather than corporate R&D.

Uses the condition (applt_seq_nr > 0) AND (invt_seq_nr > 0) to find persons
who are both applicant and inventor on the same application.

Based on EPO training query 2.4.""",
        "key_outputs": [
            "Filing authorities popular with individual inventors",
            "Application counts per office",
            "Grant rates for individual inventor filings"
        ],
        "methodology": "Filters tls207_pers_appln for persons with both applt_seq_nr and invt_seq_nr > 0",
        "estimated_seconds_first_run": 6,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                a.appln_auth AS filing_authority,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct,
                COUNT(DISTINCT pa.person_id) AS unique_inventor_applicants
            FROM tls201_appln a
            JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
            WHERE pa.applt_seq_nr > 0
              AND pa.invt_seq_nr > 0
              AND a.appln_filing_year BETWEEN 2018 AND 2023
            GROUP BY a.appln_auth
            HAVING COUNT(DISTINCT a.appln_id) >= 100
            ORDER BY applications DESC
            LIMIT 20
        """,
        "sql_template": """
            SELECT
                a.appln_auth AS filing_authority,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct,
                COUNT(DISTINCT pa.person_id) AS unique_inventor_applicants
            FROM tls201_appln a
            JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
            WHERE pa.applt_seq_nr > 0
              AND pa.invt_seq_nr > 0
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
            GROUP BY a.appln_auth
            HAVING COUNT(DISTINCT a.appln_id) >= 100
            ORDER BY applications DESC
            LIMIT 20
        """
    },

    "Q24": {
        "title": "Which universities are most active in patenting?",
        "tags": ["UNIVERSITY"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "University and research institution patent activity rankings",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies the most active universities and research institutions
by filtering for applicants in the 'UNIVERSITY' sector (psn_sector field).

This helps identify:
- Leading research universities in patent filings
- Academic technology transfer activity
- University innovation trends""",
        "key_outputs": [
            "Universities ranked by patent applications",
            "Country of institution",
            "Grant success rates",
            "Patent family counts"
        ],
        "methodology": "Filters tls206_person by psn_sector = 'UNIVERSITY'",
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                p.doc_std_name AS university_name,
                p.person_ctry_code AS country,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct,
                COUNT(DISTINCT a.docdb_family_id) AS patent_families
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND p.psn_sector = 'UNIVERSITY'
              AND a.appln_filing_year BETWEEN 2015 AND 2023
              AND p.doc_std_name IS NOT NULL
            GROUP BY p.doc_std_name, p.person_ctry_code
            HAVING COUNT(DISTINCT a.appln_id) >= 50
            ORDER BY applications DESC
            LIMIT 30
        """,
        "sql_template": """
            SELECT
                p.doc_std_name AS university_name,
                p.person_ctry_code AS country,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct,
                COUNT(DISTINCT a.docdb_family_id) AS patent_families
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND p.psn_sector = 'UNIVERSITY'
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND p.doc_std_name IS NOT NULL
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY p.doc_std_name, p.person_ctry_code
            HAVING COUNT(DISTINCT a.appln_id) >= 50
            ORDER BY applications DESC
            LIMIT 30
        """
    },

    "Q25": {
        "title": "What is the average patent family size by applicant country?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "Average number of jurisdictions where applicants from each country file their patents",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            }
        },
        "explanation": """Shows the international filing strategy by country of origin.
Higher average family sizes indicate:
- Greater international market focus
- Resources for global IP protection
- Strategic importance of foreign markets

Based on analysis patterns from EPO training materials.""",
        "key_outputs": [
            "Countries ranked by average family size",
            "Total patent families per country",
            "Distribution of filing strategies"
        ],
        "methodology": "Aggregates docdb_family_size by applicant country from tls206_person",
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 2,
        "visualization": {
            "x": "applicant_country",
            "y": "avg_family_size",
            "type": "bar"
        },
        "sql": """
            SELECT
                p.person_ctry_code AS applicant_country,
                COUNT(DISTINCT a.docdb_family_id) AS total_families,
                ROUND(AVG(a.docdb_family_size), 2) AS avg_family_size,
                MAX(a.docdb_family_size) AS max_family_size,
                COUNT(DISTINCT a.appln_id) AS total_applications
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND a.appln_filing_year BETWEEN 2018 AND 2023
              AND p.person_ctry_code IS NOT NULL
              AND a.appln_id = a.earliest_filing_id
            GROUP BY p.person_ctry_code
            HAVING COUNT(DISTINCT a.docdb_family_id) >= 1000
            ORDER BY avg_family_size DESC
            LIMIT 30
        """,
        "sql_template": """
            SELECT
                p.person_ctry_code AS applicant_country,
                COUNT(DISTINCT a.docdb_family_id) AS total_families,
                ROUND(AVG(a.docdb_family_size), 2) AS avg_family_size,
                MAX(a.docdb_family_size) AS max_family_size,
                COUNT(DISTINCT a.appln_id) AS total_applications
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND p.person_ctry_code IS NOT NULL
              AND a.appln_id = a.earliest_filing_id
            GROUP BY p.person_ctry_code
            HAVING COUNT(DISTINCT a.docdb_family_id) >= 1000
            ORDER BY avg_family_size DESC
            LIMIT 30
        """
    },

    "Q26": {
        "title": "How long does it take to get a patent granted?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Average time from filing to grant publication by patent office",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Calculates the average pendency (time-to-grant) for different patent offices.
This helps applicants understand:
- Which offices process applications faster
- Expected timeline for patent protection
- Resource planning for prosecution

Uses the first grant publication date from tls211_pat_publn.""",
        "key_outputs": [
            "Patent offices ranked by processing speed",
            "Average days to grant",
            "Number of granted patents analyzed"
        ],
        "methodology": "Calculates date difference between filing and first grant publication",
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                a.appln_auth AS patent_office,
                COUNT(DISTINCT a.appln_id) AS granted_patents,
                ROUND(AVG(DATE_DIFF(pub.publn_date, a.appln_filing_date, DAY)), 0) AS avg_days_to_grant,
                ROUND(AVG(DATE_DIFF(pub.publn_date, a.appln_filing_date, DAY)) / 365.25, 1) AS avg_years_to_grant,
                MIN(DATE_DIFF(pub.publn_date, a.appln_filing_date, DAY)) AS min_days,
                MAX(DATE_DIFF(pub.publn_date, a.appln_filing_date, DAY)) AS max_days
            FROM tls201_appln a
            JOIN tls211_pat_publn pub ON a.appln_id = pub.appln_id
            WHERE a.granted = 'Y'
              AND pub.publn_first_grant = 'Y'
              AND a.appln_filing_year BETWEEN 2015 AND 2020
              AND pub.publn_date IS NOT NULL
              AND pub.publn_date > a.appln_filing_date
              AND pub.publn_date < '9999-01-01'
            GROUP BY a.appln_auth
            HAVING COUNT(DISTINCT a.appln_id) >= 1000
            ORDER BY avg_days_to_grant ASC
            LIMIT 20
        """,
        "sql_template": """
            SELECT
                a.appln_auth AS patent_office,
                COUNT(DISTINCT a.appln_id) AS granted_patents,
                ROUND(AVG(DATE_DIFF(pub.publn_date, a.appln_filing_date, DAY)), 0) AS avg_days_to_grant,
                ROUND(AVG(DATE_DIFF(pub.publn_date, a.appln_filing_date, DAY)) / 365.25, 1) AS avg_years_to_grant,
                MIN(DATE_DIFF(pub.publn_date, a.appln_filing_date, DAY)) AS min_days,
                MAX(DATE_DIFF(pub.publn_date, a.appln_filing_date, DAY)) AS max_days
            FROM tls201_appln a
            JOIN tls211_pat_publn pub ON a.appln_id = pub.appln_id
            WHERE a.granted = 'Y'
              AND pub.publn_first_grant = 'Y'
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND pub.publn_date IS NOT NULL
              AND pub.publn_date > a.appln_filing_date
              AND pub.publn_date < '9999-01-01'
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY a.appln_auth
            HAVING COUNT(DISTINCT a.appln_id) >= 1000
            ORDER BY avg_days_to_grant ASC
            LIMIT 20
        """
    },

    "Q27": {
        "title": "Which technology fields have the highest grant rates?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Grant success rates by WIPO technology field classification",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Compares grant rates across different technology sectors using
WIPO's technology field classification. This helps:
- Identify easier vs. harder technology areas for patent prosecution
- Inform filing strategy decisions
- Understand examiner scrutiny levels by field

Uses the tls230_appln_techn_field and tls901_techn_field_ipc tables.""",
        "key_outputs": [
            "Technology fields ranked by grant rate",
            "Total applications vs. granted",
            "Sector groupings"
        ],
        "methodology": "Joins technology field tables and calculates grant rates per field",
        "estimated_seconds_first_run": 12,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                tf.techn_sector,
                tf.techn_field,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct
            FROM tls230_appln_techn_field atf
            JOIN tls901_techn_field_ipc tf ON atf.techn_field_nr = tf.techn_field_nr
            JOIN tls201_appln a ON atf.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN 2010 AND 2018
              AND atf.weight > 0.5
            GROUP BY tf.techn_sector, tf.techn_field
            HAVING COUNT(DISTINCT a.appln_id) >= 10000
            ORDER BY grant_rate_pct DESC
        """,
        "sql_template": """
            SELECT
                tf.techn_sector,
                tf.techn_field,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct
            FROM tls230_appln_techn_field atf
            JOIN tls901_techn_field_ipc tf ON atf.techn_field_nr = tf.techn_field_nr
            JOIN tls201_appln a ON atf.appln_id = a.appln_id
            WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
              AND atf.weight > 0.5
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY tf.techn_sector, tf.techn_field
            HAVING COUNT(DISTINCT a.appln_id) >= 10000
            ORDER BY grant_rate_pct DESC
        """
    },

    "Q28": {
        "title": "Which patents have dual IPC classifications?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Applications classified in multiple technology areas (cross-domain innovations)",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies patents at the intersection of multiple technology fields
by finding applications with IPC codes from different main classes.

Cross-domain innovations often represent breakthrough technologies combining
expertise from multiple fields (e.g., AI + Medical, Battery + Vehicle).

Based on EPO training query 2.7 - applications with multiple IPC classes.""",
        "key_outputs": [
            "IPC class combinations",
            "Number of cross-classified applications",
            "Technology intersection trends"
        ],
        "methodology": "Self-join on tls209_appln_ipc to find applications with multiple IPC sections",
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                SUBSTR(i1.ipc_class_symbol, 1, 4) AS ipc_class_1,
                SUBSTR(i2.ipc_class_symbol, 1, 4) AS ipc_class_2,
                COUNT(DISTINCT i1.appln_id) AS cross_classified_applications
            FROM tls209_appln_ipc i1
            JOIN tls209_appln_ipc i2 ON i1.appln_id = i2.appln_id
            JOIN tls201_appln a ON i1.appln_id = a.appln_id
            WHERE SUBSTR(i1.ipc_class_symbol, 1, 1) < SUBSTR(i2.ipc_class_symbol, 1, 1)
              AND a.appln_filing_year BETWEEN 2018 AND 2023
            GROUP BY SUBSTR(i1.ipc_class_symbol, 1, 4), SUBSTR(i2.ipc_class_symbol, 1, 4)
            HAVING COUNT(DISTINCT i1.appln_id) >= 1000
            ORDER BY cross_classified_applications DESC
            LIMIT 30
        """,
        "sql_template": """
            SELECT
                SUBSTR(i1.ipc_class_symbol, 1, 4) AS ipc_class_1,
                SUBSTR(i2.ipc_class_symbol, 1, 4) AS ipc_class_2,
                COUNT(DISTINCT i1.appln_id) AS cross_classified_applications
            FROM tls209_appln_ipc i1
            JOIN tls209_appln_ipc i2 ON i1.appln_id = i2.appln_id
            JOIN tls201_appln a ON i1.appln_id = a.appln_id
            WHERE SUBSTR(i1.ipc_class_symbol, 1, 1) < SUBSTR(i2.ipc_class_symbol, 1, 1)
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY SUBSTR(i1.ipc_class_symbol, 1, 4), SUBSTR(i2.ipc_class_symbol, 1, 4)
            HAVING COUNT(DISTINCT i1.appln_id) >= 1000
            ORDER BY cross_classified_applications DESC
            LIMIT 30
        """
    },

    # =========================================================================
    # TECHNOLOGY TRANSFER (Q18) - Original position maintained
    # =========================================================================
    "Q18": {
        "title": "What are the fastest-growing IT management subclasses?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Fastest-growing sub-classes within G06Q (IT methods for management)",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Year Range for Growth Comparison",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """This query identifies the fastest-growing G06Q sub-classes by comparing
filing activity between years. It also identifies the top 3 applicants driving growth
in each subclass.

G06Q covers IT methods for management, administration, commerce, etc.
Uses SUBSTR to extract subclass - handles variable whitespace correctly.""",
        "key_outputs": [
            "Fastest-growing G06Q subclasses by growth rate",
            "Year-over-year comparison",
            "Top 3 applicants per growing subclass"
        ],
        "estimated_seconds_first_run": 5,
        "estimated_seconds_cached": 1,
        "sql": """
            WITH g06q_subclasses AS (
                SELECT
                    SUBSTR(cpc.cpc_class_symbol, 1, 8) AS subclass,
                    a.appln_id,
                    a.appln_filing_date,
                    a.appln_filing_year
                FROM tls224_appln_cpc cpc
                JOIN tls201_appln a ON cpc.appln_id = a.appln_id
                WHERE cpc.cpc_class_symbol LIKE 'G06Q%'
                  AND a.appln_filing_year BETWEEN 2021 AND 2023
            ),
            subclass_growth AS (
                SELECT
                    subclass,
                    COUNT(*) AS total_applications,
                    COUNT(CASE WHEN appln_filing_year = 2023 THEN 1 END) AS recent_year_apps,
                    COUNT(CASE WHEN appln_filing_year = 2021 THEN 1 END) AS base_year_apps,
                    CASE
                        WHEN COUNT(CASE WHEN appln_filing_year = 2021 THEN 1 END) > 0
                        THEN (CAST(COUNT(CASE WHEN appln_filing_year = 2023 THEN 1 END) AS FLOAT64) /
                              COUNT(CASE WHEN appln_filing_year = 2021 THEN 1 END) - 1) * 100
                        ELSE NULL
                    END AS growth_rate_pct
                FROM g06q_subclasses
                GROUP BY subclass
                HAVING COUNT(*) >= 10
            ),
            top_growing_subclasses AS (
                SELECT *
                FROM subclass_growth
                WHERE growth_rate_pct IS NOT NULL
                ORDER BY growth_rate_pct DESC
                LIMIT 10
            ),
            driving_applicants AS (
                SELECT
                    tgs.subclass,
                    tgs.growth_rate_pct,
                    p.person_name,
                    p.person_ctry_code,
                    COUNT(*) AS applications_count,
                    ROW_NUMBER() OVER (PARTITION BY tgs.subclass ORDER BY COUNT(*) DESC) AS applicant_rank
                FROM top_growing_subclasses tgs
                JOIN g06q_subclasses gqs ON tgs.subclass = gqs.subclass
                JOIN tls207_pers_appln pa ON gqs.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE pa.applt_seq_nr > 0
                GROUP BY tgs.subclass, tgs.growth_rate_pct, p.person_name, p.person_ctry_code
            )
            SELECT
                da.subclass,
                ROUND(da.growth_rate_pct, 2) AS growth_rate_percent,
                da.person_name AS top_applicant,
                da.person_ctry_code AS applicant_country,
                da.applications_count AS applicant_filings,
                tgs.total_applications AS subclass_total_apps,
                tgs.recent_year_apps,
                tgs.base_year_apps
            FROM driving_applicants da
            JOIN top_growing_subclasses tgs ON da.subclass = tgs.subclass
            WHERE da.applicant_rank <= 3
            ORDER BY da.growth_rate_pct DESC, da.subclass, da.applicant_rank
        """,
        "sql_template": """
            WITH g06q_subclasses AS (
                SELECT
                    SUBSTR(cpc.cpc_class_symbol, 1, 8) AS subclass,
                    a.appln_id,
                    a.appln_filing_date,
                    a.appln_filing_year
                FROM tls224_appln_cpc cpc
                JOIN tls201_appln a ON cpc.appln_id = a.appln_id
                WHERE cpc.cpc_class_symbol LIKE 'G06Q%'
                  AND a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND a.appln_auth IN UNNEST(@jurisdictions)
            ),
            subclass_growth AS (
                SELECT
                    subclass,
                    COUNT(*) AS total_applications,
                    COUNT(CASE WHEN appln_filing_year = @year_end THEN 1 END) AS recent_year_apps,
                    COUNT(CASE WHEN appln_filing_year = @year_start THEN 1 END) AS base_year_apps,
                    CASE
                        WHEN COUNT(CASE WHEN appln_filing_year = @year_start THEN 1 END) > 0
                        THEN (CAST(COUNT(CASE WHEN appln_filing_year = @year_end THEN 1 END) AS FLOAT64) /
                              COUNT(CASE WHEN appln_filing_year = @year_start THEN 1 END) - 1) * 100
                        ELSE NULL
                    END AS growth_rate_pct
                FROM g06q_subclasses
                GROUP BY subclass
                HAVING COUNT(*) >= 10
            ),
            top_growing_subclasses AS (
                SELECT *
                FROM subclass_growth
                WHERE growth_rate_pct IS NOT NULL
                ORDER BY growth_rate_pct DESC
                LIMIT 10
            ),
            driving_applicants AS (
                SELECT
                    tgs.subclass,
                    tgs.growth_rate_pct,
                    p.person_name,
                    p.person_ctry_code,
                    COUNT(*) AS applications_count,
                    ROW_NUMBER() OVER (PARTITION BY tgs.subclass ORDER BY COUNT(*) DESC) AS applicant_rank
                FROM top_growing_subclasses tgs
                JOIN g06q_subclasses gqs ON tgs.subclass = gqs.subclass
                JOIN tls207_pers_appln pa ON gqs.appln_id = pa.appln_id
                JOIN tls206_person p ON pa.person_id = p.person_id
                WHERE pa.applt_seq_nr > 0
                GROUP BY tgs.subclass, tgs.growth_rate_pct, p.person_name, p.person_ctry_code
            )
            SELECT
                da.subclass,
                ROUND(da.growth_rate_pct, 2) AS growth_rate_percent,
                da.person_name AS top_applicant,
                da.person_ctry_code AS applicant_country,
                da.applications_count AS applicant_filings,
                tgs.total_applications AS subclass_total_apps,
                tgs.recent_year_apps,
                tgs.base_year_apps
            FROM driving_applicants da
            JOIN top_growing_subclasses tgs ON da.subclass = tgs.subclass
            WHERE da.applicant_rank <= 3
            ORDER BY da.growth_rate_pct DESC, da.subclass, da.applicant_rank
        """
    },

    # =========================================================================
    # EPO TRAINING QUERIES - BATCH 1 (Q29-Q38)
    # Source: EPO PATSTAT Sample Queries and Training Materials
    # =========================================================================
    "Q29": {
        "title": "Which patents are the most cited?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Most cited patent applications by citation count",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies the most influential patents based on family citation counts.
Uses nb_citing_docdb_fam which counts distinct DOCDB families that cite the
application or any of its family members. Citation frequency on family level
is more meaningful than publication-level citations for assessing patent impact.

High citation counts indicate technically influential patents that form
the basis for subsequent innovation.""",
        "key_outputs": [
            "Top cited patents by family citation count",
            "Application details (authority, number, date)",
            "Family size as additional importance indicator"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.1 - adapted for BigQuery",
        "estimated_seconds_first_run": 3,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                nb_citing_docdb_fam AS citation_count,
                appln_id,
                CONCAT(appln_auth, appln_nr, appln_kind) AS application_number,
                appln_auth AS authority,
                appln_filing_date,
                appln_filing_year,
                docdb_family_size,
                granted
            FROM tls201_appln
            WHERE appln_filing_year >= 2010
              AND nb_citing_docdb_fam > 0
            ORDER BY nb_citing_docdb_fam DESC
            LIMIT 50
        """,
        "sql_template": """
            SELECT
                nb_citing_docdb_fam AS citation_count,
                appln_id,
                CONCAT(appln_auth, appln_nr, appln_kind) AS application_number,
                appln_auth AS authority,
                appln_filing_date,
                appln_filing_year,
                docdb_family_size,
                granted
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN @year_start AND @year_end
              AND appln_auth IN UNNEST(@jurisdictions)
              AND nb_citing_docdb_fam > 0
            ORDER BY nb_citing_docdb_fam DESC
            LIMIT 50
        """
    },

    "Q30": {
        "title": "Who are the most active applicants by country?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Top patent applicants ranked by filing volume within a country",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies the most prolific patent applicants by their country of residence.
Uses DOCDB standardized names (doc_std_name) for better name harmonization.
Applicants are identified by applt_seq_nr > 0.

Note: Applicants are filtered by their country of residence (person_ctry_code),
not by where they file. Multinational corporations filing centrally may affect
results.""",
        "key_outputs": [
            "Top applicants ranked by application count",
            "Standardized applicant names",
            "Country of residence"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.2 - adapted for BigQuery",
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                COUNT(*) AS application_count,
                p.doc_std_name AS applicant_name,
                p.person_ctry_code AS country
            FROM tls206_person p
            JOIN tls207_pers_appln pa ON p.person_id = pa.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND a.appln_filing_year >= 2018
              AND p.person_ctry_code IS NOT NULL
              AND p.doc_std_name IS NOT NULL
            GROUP BY p.doc_std_name, p.person_ctry_code
            HAVING COUNT(*) >= 10
            ORDER BY application_count DESC
            LIMIT 50
        """,
        "sql_template": """
            SELECT
                COUNT(*) AS application_count,
                p.doc_std_name AS applicant_name,
                p.person_ctry_code AS country
            FROM tls206_person p
            JOIN tls207_pers_appln pa ON p.person_id = pa.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND a.appln_auth IN UNNEST(@jurisdictions)
              AND p.person_ctry_code IS NOT NULL
              AND p.doc_std_name IS NOT NULL
            GROUP BY p.doc_std_name, p.person_ctry_code
            HAVING COUNT(*) >= 10
            ORDER BY application_count DESC
            LIMIT 50
        """
    },

    "Q31": {
        "title": "Which applicants collaborate internationally?",
        "tags": ["PATLIB", "BUSINESS", "UNIVERSITY"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Applicants who co-file patents with partners from other countries",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies international collaboration patterns by finding applications
with co-applicants from different countries. This reveals strategic partnerships,
joint ventures, and cross-border R&D collaborations.

Both parties must be applicants (applt_seq_nr > 0) and from different countries.
Results are ranked by the number of joint applications.""",
        "key_outputs": [
            "Co-applicant pairs from different countries",
            "Number of joint applications",
            "Country combinations"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.3 - adapted for BigQuery",
        "estimated_seconds_first_run": 12,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                COUNT(*) AS joint_applications,
                p1.doc_std_name AS applicant_1,
                p1.person_ctry_code AS country_1,
                p2.doc_std_name AS applicant_2,
                p2.person_ctry_code AS country_2
            FROM tls206_person p1
            JOIN tls207_pers_appln pa1 ON p1.person_id = pa1.person_id
            JOIN tls207_pers_appln pa2 ON pa1.appln_id = pa2.appln_id
            JOIN tls206_person p2 ON pa2.person_id = p2.person_id
            JOIN tls201_appln a ON pa1.appln_id = a.appln_id
            WHERE pa1.applt_seq_nr > 0
              AND pa2.applt_seq_nr > 0
              AND p1.person_ctry_code <> p2.person_ctry_code
              AND p1.person_id < p2.person_id
              AND a.appln_filing_year >= 2018
              AND p1.doc_std_name IS NOT NULL
              AND p2.doc_std_name IS NOT NULL
            GROUP BY p1.doc_std_name, p1.person_ctry_code, p2.doc_std_name, p2.person_ctry_code
            HAVING COUNT(*) >= 3
            ORDER BY joint_applications DESC
            LIMIT 50
        """,
        "sql_template": """
            SELECT
                COUNT(*) AS joint_applications,
                p1.doc_std_name AS applicant_1,
                p1.person_ctry_code AS country_1,
                p2.doc_std_name AS applicant_2,
                p2.person_ctry_code AS country_2
            FROM tls206_person p1
            JOIN tls207_pers_appln pa1 ON p1.person_id = pa1.person_id
            JOIN tls207_pers_appln pa2 ON pa1.appln_id = pa2.appln_id
            JOIN tls206_person p2 ON pa2.person_id = p2.person_id
            JOIN tls201_appln a ON pa1.appln_id = a.appln_id
            WHERE pa1.applt_seq_nr > 0
              AND pa2.applt_seq_nr > 0
              AND p1.person_ctry_code <> p2.person_ctry_code
              AND p1.person_id < p2.person_id
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND a.appln_auth IN UNNEST(@jurisdictions)
              AND p1.doc_std_name IS NOT NULL
              AND p2.doc_std_name IS NOT NULL
            GROUP BY p1.doc_std_name, p1.person_ctry_code, p2.doc_std_name, p2.person_ctry_code
            HAVING COUNT(*) >= 3
            ORDER BY joint_applications DESC
            LIMIT 50
        """
    },

    "Q32": {
        "title": "Where are inventors also the applicants?",
        "tags": ["PATLIB", "UNIVERSITY"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "Applications where the same person is both inventor and applicant",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies applications where the inventor is also the applicant,
indicating individual inventors, small entities, or professor's privilege situations.
Common in academia and for independent inventors.

The condition (applt_seq_nr > 0) AND (invt_seq_nr > 0) selects persons
who are both applicant and inventor on the same application.""",
        "key_outputs": [
            "Applications with inventor-applicants",
            "Count by filing authority",
            "Individual inventor filing patterns"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.4 - adapted for BigQuery",
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                a.appln_auth AS authority,
                COUNT(DISTINCT a.appln_id) AS inventor_applicant_count,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted_count,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct
            FROM tls201_appln a
            JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
            WHERE pa.applt_seq_nr > 0
              AND pa.invt_seq_nr > 0
              AND a.appln_filing_year >= 2015
            GROUP BY a.appln_auth
            HAVING COUNT(DISTINCT a.appln_id) >= 100
            ORDER BY inventor_applicant_count DESC
            LIMIT 30
        """,
        "sql_template": """
            SELECT
                a.appln_auth AS authority,
                COUNT(DISTINCT a.appln_id) AS inventor_applicant_count,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted_count,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct
            FROM tls201_appln a
            JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
            WHERE pa.applt_seq_nr > 0
              AND pa.invt_seq_nr > 0
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY a.appln_auth
            HAVING COUNT(DISTINCT a.appln_id) >= 10
            ORDER BY inventor_applicant_count DESC
            LIMIT 30
        """
    },

    "Q33": {
        "title": "What are first filings vs. subsequent filings?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Analysis of first filings (priority applications) vs. subsequent filings",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Distinguishes between first filings (priority applications where
appln_id = earliest_filing_id) and subsequent filings (extensions, nationals, etc.).
First filings represent genuine new inventions, while subsequent filings
show how inventions are extended globally.

This ratio helps understand innovation vs. globalization strategies.""",
        "key_outputs": [
            "First filing counts (new inventions)",
            "Subsequent filing counts (extensions)",
            "First filing ratio by year"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.5 concept - adapted for BigQuery",
        "estimated_seconds_first_run": 5,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                appln_filing_year,
                COUNT(*) AS total_applications,
                COUNT(CASE WHEN appln_id = earliest_filing_id THEN 1 END) AS first_filings,
                COUNT(CASE WHEN appln_id <> earliest_filing_id THEN 1 END) AS subsequent_filings,
                ROUND(COUNT(CASE WHEN appln_id = earliest_filing_id THEN 1 END) * 100.0 /
                      NULLIF(COUNT(*), 0), 1) AS first_filing_pct
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN 2015 AND 2023
              AND earliest_filing_id > 0
            GROUP BY appln_filing_year
            ORDER BY appln_filing_year DESC
        """,
        "sql_template": """
            SELECT
                appln_filing_year,
                COUNT(*) AS total_applications,
                COUNT(CASE WHEN appln_id = earliest_filing_id THEN 1 END) AS first_filings,
                COUNT(CASE WHEN appln_id <> earliest_filing_id THEN 1 END) AS subsequent_filings,
                ROUND(COUNT(CASE WHEN appln_id = earliest_filing_id THEN 1 END) * 100.0 /
                      NULLIF(COUNT(*), 0), 1) AS first_filing_pct
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN @year_start AND @year_end
              AND appln_auth IN UNNEST(@jurisdictions)
              AND earliest_filing_id > 0
            GROUP BY appln_filing_year
            ORDER BY appln_filing_year ASC
        """
    },

    "Q34": {
        "title": "Which patents combine multiple technology areas?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Applications classified in multiple distinct IPC classes",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies patents that span multiple technology domains by having
classifications in different IPC main classes (e.g., both C01B and H01M for
battery chemistry). Cross-domain patents often represent innovative combinations
and may indicate emerging technology convergence areas.

Uses EXISTS subqueries to find applications with both specified IPC classes.""",
        "key_outputs": [
            "Cross-classified application counts",
            "Technology intersection patterns",
            "Multi-domain innovation indicators"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.7 - adapted for BigQuery",
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 2,
        "sql": """
            WITH cross_classified AS (
                SELECT
                    a.appln_id,
                    a.appln_auth,
                    a.appln_filing_year,
                    a.granted
                FROM tls201_appln a
                WHERE a.appln_filing_year >= 2018
                  AND EXISTS (
                    SELECT 1 FROM tls209_appln_ipc i1
                    WHERE i1.appln_id = a.appln_id
                      AND i1.ipc_class_symbol LIKE 'H01M%'
                  )
                  AND EXISTS (
                    SELECT 1 FROM tls209_appln_ipc i2
                    WHERE i2.appln_id = a.appln_id
                      AND i2.ipc_class_symbol LIKE 'C01B%'
                  )
            )
            SELECT
                appln_auth AS authority,
                appln_filing_year,
                COUNT(*) AS cross_classified_count,
                COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted_count
            FROM cross_classified
            GROUP BY appln_auth, appln_filing_year
            HAVING COUNT(*) >= 5
            ORDER BY appln_filing_year DESC, cross_classified_count DESC
        """,
        "sql_template": """
            WITH cross_classified AS (
                SELECT
                    a.appln_id,
                    a.appln_auth,
                    a.appln_filing_year,
                    a.granted
                FROM tls201_appln a
                WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND a.appln_auth IN UNNEST(@jurisdictions)
                  AND EXISTS (
                    SELECT 1 FROM tls209_appln_ipc i1
                    WHERE i1.appln_id = a.appln_id
                      AND i1.ipc_class_symbol LIKE 'H01M%'
                  )
                  AND EXISTS (
                    SELECT 1 FROM tls209_appln_ipc i2
                    WHERE i2.appln_id = a.appln_id
                      AND i2.ipc_class_symbol LIKE 'C01B%'
                  )
            )
            SELECT
                appln_auth AS authority,
                appln_filing_year,
                COUNT(*) AS cross_classified_count,
                COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted_count
            FROM cross_classified
            GROUP BY appln_auth, appln_filing_year
            ORDER BY appln_filing_year ASC, cross_classified_count DESC
        """
    },

    "Q35": {
        "title": "Which offices publish patents the fastest?",
        "tags": ["PATLIB"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "Patent offices ranked by speed from filing to first publication",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Analyzes which patent offices publish applications fastest after filing.
Standard publication is 18 months after filing, but some offices publish earlier.
Early publication affects prior art considerations and competitive intelligence.

Uses DATE_DIFF to calculate months between filing and earliest publication date.""",
        "key_outputs": [
            "Average months to publication by office",
            "Fast-track publication counts",
            "Office efficiency comparison"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.8 - adapted for BigQuery",
        "estimated_seconds_first_run": 6,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                appln_auth AS authority,
                COUNT(*) AS total_applications,
                COUNT(CASE WHEN DATE_DIFF(earliest_publn_date, appln_filing_date, MONTH) <= 15
                           AND earliest_publn_date < '9999-01-01' THEN 1 END) AS fast_publications,
                ROUND(AVG(CASE WHEN earliest_publn_date < '9999-01-01'
                          THEN DATE_DIFF(earliest_publn_date, appln_filing_date, MONTH) END), 1) AS avg_months_to_publn,
                ROUND(COUNT(CASE WHEN DATE_DIFF(earliest_publn_date, appln_filing_date, MONTH) <= 15
                           AND earliest_publn_date < '9999-01-01' THEN 1 END) * 100.0 /
                      NULLIF(COUNT(*), 0), 1) AS fast_publn_pct
            FROM tls201_appln
            WHERE appln_filing_year = 2020
              AND appln_filing_date IS NOT NULL
              AND appln_filing_date > '1900-01-01'
            GROUP BY appln_auth
            HAVING COUNT(*) >= 1000
            ORDER BY avg_months_to_publn ASC
            LIMIT 30
        """,
        "sql_template": """
            SELECT
                appln_auth AS authority,
                COUNT(*) AS total_applications,
                COUNT(CASE WHEN DATE_DIFF(earliest_publn_date, appln_filing_date, MONTH) <= 15
                           AND earliest_publn_date < '9999-01-01' THEN 1 END) AS fast_publications,
                ROUND(AVG(CASE WHEN earliest_publn_date < '9999-01-01'
                          THEN DATE_DIFF(earliest_publn_date, appln_filing_date, MONTH) END), 1) AS avg_months_to_publn,
                ROUND(COUNT(CASE WHEN DATE_DIFF(earliest_publn_date, appln_filing_date, MONTH) <= 15
                           AND earliest_publn_date < '9999-01-01' THEN 1 END) * 100.0 /
                      NULLIF(COUNT(*), 0), 1) AS fast_publn_pct
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN @year_start AND @year_end
              AND appln_auth IN UNNEST(@jurisdictions)
              AND appln_filing_date IS NOT NULL
              AND appln_filing_date > '1900-01-01'
            GROUP BY appln_auth
            HAVING COUNT(*) >= 100
            ORDER BY avg_months_to_publn ASC
            LIMIT 30
        """
    },

    "Q36": {
        "title": "Who are the inventors for top research organizations?",
        "tags": ["UNIVERSITY", "BUSINESS"],
        "category": "Competitors",
        "platforms": ["bigquery", "tip"],
        "description": "Inventors associated with major patent-filing organizations",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies inventors (invt_seq_nr > 0) associated with applications
from major patent-filing organizations. Shows which individuals drive innovation
at large institutions and their technology focus areas (via IPC classes).

Uses earliest_filing_year to focus on genuine invention dates rather than
subsequent filing dates.""",
        "key_outputs": [
            "Top inventors by organization",
            "Inventor country of residence",
            "Technology areas (IPC classes)"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.9 - adapted for BigQuery",
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 2,
        "sql": """
            WITH top_applicants AS (
                SELECT
                    p.person_id,
                    p.doc_std_name,
                    COUNT(DISTINCT a.appln_id) AS app_count
                FROM tls206_person p
                JOIN tls207_pers_appln pa ON p.person_id = pa.person_id
                JOIN tls201_appln a ON pa.appln_id = a.appln_id
                WHERE pa.applt_seq_nr > 0
                  AND a.earliest_filing_year >= 2018
                  AND p.psn_sector IN ('COMPANY', 'GOV NON-PROFIT', 'UNIVERSITY')
                GROUP BY p.person_id, p.doc_std_name
                ORDER BY app_count DESC
                LIMIT 20
            ),
            org_inventors AS (
                SELECT DISTINCT
                    ta.doc_std_name AS organization,
                    inv.person_name AS inventor_name,
                    inv.person_ctry_code AS inventor_country,
                    COUNT(DISTINCT a.appln_id) AS invention_count
                FROM top_applicants ta
                JOIN tls207_pers_appln pa_org ON ta.person_id = pa_org.person_id
                JOIN tls207_pers_appln pa_inv ON pa_org.appln_id = pa_inv.appln_id
                JOIN tls206_person inv ON pa_inv.person_id = inv.person_id
                JOIN tls201_appln a ON pa_org.appln_id = a.appln_id
                WHERE pa_org.applt_seq_nr > 0
                  AND pa_inv.invt_seq_nr > 0
                  AND a.earliest_filing_year >= 2018
                GROUP BY ta.doc_std_name, inv.person_name, inv.person_ctry_code
            )
            SELECT
                organization,
                inventor_name,
                inventor_country,
                invention_count
            FROM org_inventors
            WHERE invention_count >= 3
            ORDER BY organization, invention_count DESC
            LIMIT 100
        """,
        "sql_template": """
            WITH top_applicants AS (
                SELECT
                    p.person_id,
                    p.doc_std_name,
                    COUNT(DISTINCT a.appln_id) AS app_count
                FROM tls206_person p
                JOIN tls207_pers_appln pa ON p.person_id = pa.person_id
                JOIN tls201_appln a ON pa.appln_id = a.appln_id
                WHERE pa.applt_seq_nr > 0
                  AND a.earliest_filing_year BETWEEN @year_start AND @year_end
                  AND a.appln_auth IN UNNEST(@jurisdictions)
                  AND p.psn_sector IN ('COMPANY', 'GOV NON-PROFIT', 'UNIVERSITY')
                GROUP BY p.person_id, p.doc_std_name
                ORDER BY app_count DESC
                LIMIT 20
            ),
            org_inventors AS (
                SELECT DISTINCT
                    ta.doc_std_name AS organization,
                    inv.person_name AS inventor_name,
                    inv.person_ctry_code AS inventor_country,
                    COUNT(DISTINCT a.appln_id) AS invention_count
                FROM top_applicants ta
                JOIN tls207_pers_appln pa_org ON ta.person_id = pa_org.person_id
                JOIN tls207_pers_appln pa_inv ON pa_org.appln_id = pa_inv.appln_id
                JOIN tls206_person inv ON pa_inv.person_id = inv.person_id
                JOIN tls201_appln a ON pa_org.appln_id = a.appln_id
                WHERE pa_org.applt_seq_nr > 0
                  AND pa_inv.invt_seq_nr > 0
                  AND a.earliest_filing_year BETWEEN @year_start AND @year_end
                GROUP BY ta.doc_std_name, inv.person_name, inv.person_ctry_code
            )
            SELECT
                organization,
                inventor_name,
                inventor_country,
                invention_count
            FROM org_inventors
            WHERE invention_count >= 2
            ORDER BY organization, invention_count DESC
            LIMIT 100
        """
    },

    "Q37": {
        "title": "What are the largest patent families?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Largest DOCDB patent families by number of family members",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies the largest patent families (DOCDB simple families).
Large families indicate inventions with broad geographic protection strategies
or high commercial value. Uses docdb_family_size for efficient querying.

DOCDB families group applications sharing the same priority, representing
essentially the same invention across different jurisdictions.""",
        "key_outputs": [
            "Largest families by member count",
            "Family ID and representative application",
            "Filing timeline"
        ],
        "methodology": "Based on EPO PATSTAT sample query 2.10 - adapted for BigQuery",
        "estimated_seconds_first_run": 4,
        "estimated_seconds_cached": 1,
        "sql": """
            WITH large_families AS (
                SELECT DISTINCT
                    docdb_family_id,
                    docdb_family_size
                FROM tls201_appln
                WHERE docdb_family_id > 0
                  AND docdb_family_size >= 50
                ORDER BY docdb_family_size DESC
                LIMIT 20
            )
            SELECT
                lf.docdb_family_id,
                lf.docdb_family_size,
                a.appln_id,
                a.appln_auth,
                a.appln_nr,
                a.appln_filing_date,
                a.earliest_filing_date,
                a.nb_citing_docdb_fam AS citations
            FROM large_families lf
            JOIN tls201_appln a ON lf.docdb_family_id = a.docdb_family_id
            WHERE a.appln_id = a.earliest_filing_id
            ORDER BY lf.docdb_family_size DESC, a.appln_filing_date ASC
        """,
        "sql_template": """
            WITH large_families AS (
                SELECT DISTINCT
                    docdb_family_id,
                    docdb_family_size
                FROM tls201_appln
                WHERE docdb_family_id > 0
                  AND docdb_family_size >= 20
                  AND appln_filing_year BETWEEN @year_start AND @year_end
                  AND appln_auth IN UNNEST(@jurisdictions)
                ORDER BY docdb_family_size DESC
                LIMIT 30
            )
            SELECT
                lf.docdb_family_id,
                lf.docdb_family_size,
                a.appln_id,
                a.appln_auth,
                a.appln_nr,
                a.appln_filing_date,
                a.earliest_filing_date,
                a.nb_citing_docdb_fam AS citations
            FROM large_families lf
            JOIN tls201_appln a ON lf.docdb_family_id = a.docdb_family_id
            WHERE a.appln_id = a.earliest_filing_id
            ORDER BY lf.docdb_family_size DESC, a.appln_filing_date ASC
        """
    },

    "Q38": {
        "title": "How do patent families spread geographically?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "Geographic distribution of patent family filings",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Analyzes how inventions (represented by DOCDB families) are protected
across different jurisdictions. Shows which filing authorities are most common
for family extensions, revealing global patent strategy patterns.

Larger average family sizes indicate jurisdictions where applicants pursue
broader global protection.""",
        "key_outputs": [
            "Filing authorities by family presence",
            "Average family size per jurisdiction",
            "Global protection patterns"
        ],
        "methodology": "Derived from EPO PATSTAT sample query 2.10 concepts - BigQuery",
        "estimated_seconds_first_run": 6,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                appln_auth AS authority,
                COUNT(DISTINCT appln_id) AS applications,
                COUNT(DISTINCT docdb_family_id) AS unique_families,
                ROUND(AVG(docdb_family_size), 1) AS avg_family_size,
                ROUND(COUNT(DISTINCT appln_id) * 1.0 / NULLIF(COUNT(DISTINCT docdb_family_id), 0), 2) AS apps_per_family
            FROM tls201_appln
            WHERE appln_filing_year >= 2018
              AND docdb_family_id > 0
            GROUP BY appln_auth
            HAVING COUNT(DISTINCT appln_id) >= 1000
            ORDER BY unique_families DESC
            LIMIT 30
        """,
        "sql_template": """
            SELECT
                appln_auth AS authority,
                COUNT(DISTINCT appln_id) AS applications,
                COUNT(DISTINCT docdb_family_id) AS unique_families,
                ROUND(AVG(docdb_family_size), 1) AS avg_family_size,
                ROUND(COUNT(DISTINCT appln_id) * 1.0 / NULLIF(COUNT(DISTINCT docdb_family_id), 0), 2) AS apps_per_family
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN @year_start AND @year_end
              AND appln_auth IN UNNEST(@jurisdictions)
              AND docdb_family_id > 0
            GROUP BY appln_auth
            HAVING COUNT(DISTINCT appln_id) >= 100
            ORDER BY unique_families DESC
            LIMIT 30
        """
    },

    # =========================================================================
    # EPO TRAINING QUERIES - BATCH 2 (Q39-Q42)
    # Source: Derived from EPO training concepts and category gap analysis
    # =========================================================================
    "Q39": {
        "title": "How have grant rates changed over time?",
        "tags": ["PATLIB", "UNIVERSITY"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Patent grant rate trends by year and filing authority",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "CN", "JP", "KR"],
                "required": True
            }
        },
        "explanation": """Analyzes how patent grant rates have evolved over time across different
patent offices. Grant rate is calculated as the percentage of applications
that received a grant (granted = 'Y').

Note: Recent years may show lower grant rates due to pendency - applications
are still being examined. Typical examination takes 3-5 years.

Useful for understanding examination rigor and success rates across offices.""",
        "key_outputs": [
            "Grant rates by year",
            "Year-over-year grant rate changes",
            "Comparison across patent offices"
        ],
        "methodology": "Derived from EPO training concepts - grant analysis",
        "estimated_seconds_first_run": 4,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                appln_filing_year,
                appln_auth AS authority,
                COUNT(*) AS total_applications,
                COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted_count,
                ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 /
                      NULLIF(COUNT(*), 0), 1) AS grant_rate_pct
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN 2010 AND 2020
              AND appln_auth IN ('EP', 'US', 'CN', 'JP', 'KR')
            GROUP BY appln_filing_year, appln_auth
            ORDER BY appln_auth, appln_filing_year ASC
        """,
        "sql_template": """
            SELECT
                appln_filing_year,
                appln_auth AS authority,
                COUNT(*) AS total_applications,
                COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted_count,
                ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 /
                      NULLIF(COUNT(*), 0), 1) AS grant_rate_pct
            FROM tls201_appln
            WHERE appln_filing_year BETWEEN @year_start AND @year_end
              AND appln_auth IN UNNEST(@jurisdictions)
            GROUP BY appln_filing_year, appln_auth
            ORDER BY appln_auth, appln_filing_year ASC
        """
    },

    "Q40": {
        "title": "How are PCT applications distributed globally?",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Regional",
        "platforms": ["bigquery", "tip"],
        "description": "PCT international application distribution by receiving office",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            }
        },
        "explanation": """Analyzes Patent Cooperation Treaty (PCT) international applications
by receiving office. PCT applications (appln_kind = 'W') are filed at
receiving offices before entering national/regional phases.

The receiving_office field shows where the PCT was initially filed.
This reveals which offices handle the most international filings and
indicates the geographic origin of innovations seeking global protection.""",
        "key_outputs": [
            "PCT applications by receiving office",
            "Market share of receiving offices",
            "Trends in international filing patterns"
        ],
        "methodology": "Derived from EPO training concepts - PCT analysis",
        "estimated_seconds_first_run": 5,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                receiving_office,
                COUNT(*) AS pct_applications,
                COUNT(DISTINCT docdb_family_id) AS unique_inventions,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_share
            FROM tls201_appln
            WHERE appln_kind = 'W'
              AND appln_filing_year >= 2018
              AND receiving_office IS NOT NULL
              AND receiving_office <> ''
            GROUP BY receiving_office
            HAVING COUNT(*) >= 100
            ORDER BY pct_applications DESC
            LIMIT 25
        """,
        "sql_template": """
            SELECT
                receiving_office,
                COUNT(*) AS pct_applications,
                COUNT(DISTINCT docdb_family_id) AS unique_inventions,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS pct_share
            FROM tls201_appln
            WHERE appln_kind = 'W'
              AND appln_filing_year BETWEEN @year_start AND @year_end
              AND receiving_office IS NOT NULL
              AND receiving_office <> ''
            GROUP BY receiving_office
            HAVING COUNT(*) >= 10
            ORDER BY pct_applications DESC
            LIMIT 25
        """
    },

    "Q41": {
        "title": "How do universities compare to corporations in patenting?",
        "tags": ["UNIVERSITY", "BUSINESS"],
        "category": "Trends",
        "platforms": ["bigquery", "tip"],
        "description": "Patent filing comparison between universities and companies",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Compares patent activity between universities (psn_sector = 'UNIVERSITY')
and companies (psn_sector = 'COMPANY'). Shows relative filing volumes,
grant success rates, and citation impact.

University patents often represent early-stage research with potential
for licensing. Corporate patents typically protect commercial products.
The citation rate comparison indicates research vs. commercial focus.""",
        "key_outputs": [
            "Filing volumes by sector",
            "Grant rates by sector",
            "Average citations (research impact indicator)"
        ],
        "methodology": "Derived from EPO training concepts - sector analysis",
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 2,
        "sql": """
            SELECT
                p.psn_sector AS sector,
                a.appln_filing_year,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct,
                ROUND(AVG(a.nb_citing_docdb_fam), 2) AS avg_citations
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND p.psn_sector IN ('UNIVERSITY', 'COMPANY')
              AND a.appln_filing_year BETWEEN 2015 AND 2020
            GROUP BY p.psn_sector, a.appln_filing_year
            ORDER BY p.psn_sector, a.appln_filing_year ASC
        """,
        "sql_template": """
            SELECT
                p.psn_sector AS sector,
                a.appln_filing_year,
                COUNT(DISTINCT a.appln_id) AS applications,
                COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) AS granted,
                ROUND(COUNT(DISTINCT CASE WHEN a.granted = 'Y' THEN a.appln_id END) * 100.0 /
                      NULLIF(COUNT(DISTINCT a.appln_id), 0), 1) AS grant_rate_pct,
                ROUND(AVG(a.nb_citing_docdb_fam), 2) AS avg_citations
            FROM tls207_pers_appln pa
            JOIN tls206_person p ON pa.person_id = p.person_id
            JOIN tls201_appln a ON pa.appln_id = a.appln_id
            WHERE pa.applt_seq_nr > 0
              AND p.psn_sector IN ('UNIVERSITY', 'COMPANY')
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND a.appln_auth IN UNNEST(@jurisdictions)
            GROUP BY p.psn_sector, a.appln_filing_year
            ORDER BY p.psn_sector, a.appln_filing_year ASC
        """
    },

    "Q42": {
        "title": "Which CPC subclasses are growing fastest?",
        "tags": ["BUSINESS", "UNIVERSITY"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Fastest-growing CPC technology subclasses by filing growth",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Year Range for Growth Comparison",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            },
            "jurisdictions": {
                "type": "multiselect",
                "label": "Patent Offices",
                "options": "jurisdictions",
                "defaults": ["EP", "US", "DE"],
                "required": True
            }
        },
        "explanation": """Identifies emerging technology areas by analyzing CPC subclass growth.
Compares filing volumes between two periods to calculate growth rates.
High-growth subclasses may indicate emerging technologies or increased
R&D investment in specific domains.

Minimum threshold ensures statistical significance. Growth rate
is calculated as percentage change from base year to recent year.""",
        "key_outputs": [
            "Top growing CPC subclasses",
            "Growth rate percentages",
            "Filing volumes by period"
        ],
        "methodology": "Derived from EPO training concepts - technology trends",
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 2,
        "sql": """
            WITH cpc_trends AS (
                SELECT
                    SUBSTR(cpc.cpc_class_symbol, 1, 4) AS cpc_subclass,
                    COUNT(CASE WHEN a.appln_filing_year BETWEEN 2018 AND 2019 THEN 1 END) AS base_period,
                    COUNT(CASE WHEN a.appln_filing_year BETWEEN 2021 AND 2022 THEN 1 END) AS recent_period
                FROM tls224_appln_cpc cpc
                JOIN tls201_appln a ON cpc.appln_id = a.appln_id
                WHERE a.appln_filing_year BETWEEN 2018 AND 2022
                GROUP BY SUBSTR(cpc.cpc_class_symbol, 1, 4)
                HAVING COUNT(CASE WHEN a.appln_filing_year BETWEEN 2018 AND 2019 THEN 1 END) >= 1000
            )
            SELECT
                cpc_subclass,
                base_period,
                recent_period,
                recent_period - base_period AS absolute_growth,
                ROUND((recent_period - base_period) * 100.0 / NULLIF(base_period, 0), 1) AS growth_rate_pct
            FROM cpc_trends
            WHERE recent_period > base_period
            ORDER BY growth_rate_pct DESC
            LIMIT 25
        """,
        "sql_template": """
            WITH cpc_trends AS (
                SELECT
                    SUBSTR(cpc.cpc_class_symbol, 1, 4) AS cpc_subclass,
                    COUNT(CASE WHEN a.appln_filing_year = @year_start THEN 1 END) AS base_period,
                    COUNT(CASE WHEN a.appln_filing_year = @year_end THEN 1 END) AS recent_period
                FROM tls224_appln_cpc cpc
                JOIN tls201_appln a ON cpc.appln_id = a.appln_id
                WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND a.appln_auth IN UNNEST(@jurisdictions)
                GROUP BY SUBSTR(cpc.cpc_class_symbol, 1, 4)
                HAVING COUNT(CASE WHEN a.appln_filing_year = @year_start THEN 1 END) >= 100
            )
            SELECT
                cpc_subclass,
                base_period,
                recent_period,
                recent_period - base_period AS absolute_growth,
                ROUND((recent_period - base_period) * 100.0 / NULLIF(base_period, 0), 1) AS growth_rate_pct
            FROM cpc_trends
            WHERE recent_period > base_period
            ORDER BY growth_rate_pct DESC
            LIMIT 25
        """
    },

    # =========================================================================
    # CLASSIFICATION QUERIES (Q54-Q58) - BigQuery only
    # These queries use IPC/CPC hierarchy tables not available on EPO TIP.
    # =========================================================================
    "Q54": {
        "title": "What does an IPC or CPC class mean?",
        "tags": ["PATLIB"],
        "category": "Classification",
        "platforms": ["bigquery"],
        "description": "Look up any IPC or CPC classification symbol to get its full title, hierarchy path, and definition",
        "parameters": {
            "classification_symbol": {
                "type": "text",
                "label": "Classification Symbol (e.g. A61B, G06N10/00, Y02E)",
                "defaults": "A61B",
                "placeholder": "e.g., A61B, H04L29/06, Y02E",
                "required": True
            },
            "system": {
                "type": "select",
                "label": "Classification System",
                "options": ["IPC", "CPC"],
                "defaults": "IPC",
                "required": True
            }
        },
        "explanation": """Looks up a classification symbol in the IPC (International Patent Classification)
or CPC (Cooperative Patent Classification) hierarchy and returns:
- The symbol's title and full breadcrumb path through the hierarchy
- Section, class, and subclass context
- WIPO definition text (where available, ~2,148 IPC symbols have definitions)
- Hierarchy level and parent symbol

Supports lookup at any level: section (A), class (A61), subclass (A61B),
main group (A61B6/00), or subgroup (A61B6/03). The symbol is matched
flexibly against symbol_short.

Note: This query uses classification tables only available on BigQuery,
not on EPO TIP.""",
        "key_outputs": [
            "Symbol and short form",
            "English title",
            "Full breadcrumb path",
            "Section/class/subclass titles",
            "Definition text (if available)",
            "Hierarchy level and kind"
        ],
        "estimated_seconds_first_run": 2,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                symbol_short,
                kind,
                level,
                title_en,
                title_full,
                section_title,
                class_title,
                subclass_title,
                additional_content AS definition,
                parent_short,
                symbol_patstat
            FROM tls_ipc_hierarchy
            WHERE UPPER(REPLACE(symbol_short, ' ', '')) LIKE UPPER(REPLACE('A61B', ' ', '')) || '%'
            ORDER BY level, symbol_short
            LIMIT 50
        """,
        "sql_template": """
            SELECT
                symbol_short,
                kind,
                level,
                title_en,
                title_full,
                section_title,
                class_title,
                subclass_title,
                additional_content AS definition,
                parent_short,
                symbol_patstat
            FROM tls_ipc_hierarchy
            WHERE UPPER(REPLACE(symbol_short, ' ', '')) LIKE UPPER(REPLACE(@classification_symbol, ' ', '')) || '%'
            ORDER BY level, symbol_short
            LIMIT 50
        """
    },
    "Q55": {
        "title": "Find IPC classes by keyword",
        "tags": ["PATLIB", "BUSINESS"],
        "category": "Classification",
        "platforms": ["bigquery"],
        "description": "Search the WIPO catchword index to discover IPC symbols by technology keyword",
        "parameters": {
            "keyword": {
                "type": "text",
                "label": "Technology Keyword (e.g. laser, battery, robot)",
                "defaults": "laser",
                "placeholder": "e.g., laser, battery, robot, pharmaceutical",
                "required": True
            }
        },
        "explanation": """Searches the WIPO IPC Catchword Index (21,361 entries) to find IPC classification
symbols related to a technology keyword. This is the official WIPO keyword-to-IPC mapping.

The catchword index maps natural-language technology terms to their corresponding
IPC symbols. For example, searching for 'laser' finds symbols like B23K26/00 (laser
welding), H01S (laser devices), A61B18/20 (laser surgery), etc.

Results include the full IPC title from the hierarchy table for immediate understanding.
Use this when you know the technology but not the IPC code.

Note: This query uses classification tables only available on BigQuery,
not on EPO TIP.""",
        "key_outputs": [
            "Matching catchwords",
            "IPC symbols with titles",
            "Section and subclass context",
            "Primary index term grouping"
        ],
        "estimated_seconds_first_run": 2,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                c.catchword,
                c.symbol_short,
                h.title_en,
                h.section_title,
                h.subclass_title,
                c.parent_catchword
            FROM tls_ipc_catchword c
            LEFT JOIN tls_ipc_hierarchy h ON c.symbol = h.symbol
            WHERE LOWER(c.catchword) LIKE '%laser%'
            ORDER BY c.parent_catchword, c.catchword
            LIMIT 50
        """,
        "sql_template": """
            SELECT
                c.catchword,
                c.symbol_short,
                h.title_en,
                h.section_title,
                h.subclass_title,
                c.parent_catchword
            FROM tls_ipc_catchword c
            LEFT JOIN tls_ipc_hierarchy h ON c.symbol = h.symbol
            WHERE LOWER(c.catchword) LIKE '%' || LOWER(@keyword) || '%'
            ORDER BY c.parent_catchword, c.catchword
            LIMIT 50
        """
    },
    "Q56": {
        "title": "What IPC codes changed in the latest revision?",
        "tags": ["PATLIB"],
        "category": "Classification",
        "platforms": ["bigquery"],
        "description": "Show created, deleted, and modified IPC symbols between versions 2025.01 and 2026.01",
        "parameters": {
            "modification_type": {
                "type": "select",
                "label": "Change Type",
                "options": ["all", "c", "d", "m"],
                "defaults": "all",
                "required": True
            }
        },
        "explanation": """Shows changes between IPC editions 2025.01 and 2026.01 from the official
WIPO concordance table (1,193 entries).

Change types:
- Created (c): New symbols added to the IPC
- Deleted (d): Symbols removed from the IPC
- Modified (m): Symbols whose scope or definition was changed

The 2026.01 revision notably restructured semiconductor classifications, moving
many codes from H01L to new H10H, H10K, H10W classes (projects C518/C519).

Each change is linked to a WIPO revision project code and shows the
default reclassification path where applicable.

Note: This query uses classification tables only available on BigQuery,
not on EPO TIP.""",
        "key_outputs": [
            "Source and target IPC symbols",
            "Change type (created/deleted/modified)",
            "New symbol title",
            "WIPO revision project code",
            "Default reclassification flag"
        ],
        "estimated_seconds_first_run": 2,
        "estimated_seconds_cached": 1,
        "sql": """
            SELECT
                con.modification,
                CASE con.modification
                    WHEN 'c' THEN 'Created'
                    WHEN 'd' THEN 'Deleted'
                    WHEN 'm' THEN 'Modified'
                END AS change_type,
                con.from_symbol_patstat AS from_code,
                con.to_symbol_patstat AS to_code,
                h_to.title_en AS new_title,
                h_to.subclass_title,
                con.default_reclassification,
                con.revision_project
            FROM tls_ipc_concordance con
            LEFT JOIN tls_ipc_hierarchy h_to ON con.to_symbol = h_to.symbol
            ORDER BY con.modification, con.revision_project, con.from_symbol_patstat
        """,
        "sql_template": """
            SELECT
                con.modification,
                CASE con.modification
                    WHEN 'c' THEN 'Created'
                    WHEN 'd' THEN 'Deleted'
                    WHEN 'm' THEN 'Modified'
                END AS change_type,
                con.from_symbol_patstat AS from_code,
                con.to_symbol_patstat AS to_code,
                h_to.title_en AS new_title,
                h_to.subclass_title,
                con.default_reclassification,
                con.revision_project
            FROM tls_ipc_concordance con
            LEFT JOIN tls_ipc_hierarchy h_to ON con.to_symbol = h_to.symbol
            WHERE @modification_type = 'all' OR con.modification = @modification_type
            ORDER BY con.modification, con.revision_project, con.from_symbol_patstat
        """
    },
    "Q57": {
        "title": "How many patents use deprecated IPC codes?",
        "tags": ["PATLIB"],
        "category": "Classification",
        "platforms": ["bigquery"],
        "description": "Analyze active vs. deprecated IPC code usage in patent data to understand classification coverage",
        "parameters": {
            "year_range": {
                "type": "year_range",
                "label": "Filing Year Range",
                "default_start": 2014,
                "default_end": 2023,
                "required": True
            }
        },
        "explanation": """Analyzes how many IPC codes used in patent applications are still active
versus deprecated in the current IPC 2026.01 edition.

The tls_ipc_everused table contains 92,856 IPC symbols that have ever been used
since 1968, including deprecated ones. This query cross-references patent
application IPC codes against this inventory to show:
- How many distinct codes are active vs. deprecated
- How many patent applications use deprecated codes
- The most-used deprecated codes (potential reclassification candidates)

Useful for data quality assessment and understanding historical classification changes.

Note: This query uses classification tables only available on BigQuery,
not on EPO TIP.""",
        "key_outputs": [
            "Count of active vs deprecated IPC codes in use",
            "Patent application counts per status",
            "Top deprecated codes with usage counts",
            "Coverage statistics"
        ],
        "estimated_seconds_first_run": 10,
        "estimated_seconds_cached": 2,
        "sql": """
            WITH code_status AS (
                SELECT
                    CASE WHEN e.is_active IS TRUE THEN 'Active'
                         WHEN e.is_active IS FALSE THEN 'Deprecated'
                         ELSE 'Unknown (not in everused)'
                    END AS ipc_status,
                    COUNT(DISTINCT ipc.ipc_class_symbol) AS distinct_codes,
                    COUNT(DISTINCT ipc.appln_id) AS patent_applications
                FROM tls209_appln_ipc ipc
                JOIN tls201_appln a ON ipc.appln_id = a.appln_id
                LEFT JOIN tls_ipc_everused e ON ipc.ipc_class_symbol = e.symbol_patstat
                WHERE a.appln_filing_year BETWEEN 2014 AND 2023
                GROUP BY 1
            ),
            top_deprecated AS (
                SELECT
                    ipc.ipc_class_symbol,
                    e.introduced_date,
                    e.deprecated_date,
                    COUNT(DISTINCT ipc.appln_id) AS patent_count
                FROM tls209_appln_ipc ipc
                JOIN tls201_appln a ON ipc.appln_id = a.appln_id
                JOIN tls_ipc_everused e ON ipc.ipc_class_symbol = e.symbol_patstat
                WHERE a.appln_filing_year BETWEEN 2014 AND 2023
                  AND e.is_active IS FALSE
                GROUP BY 1, 2, 3
                ORDER BY patent_count DESC
                LIMIT 20
            )
            SELECT 'Summary' AS result_type, ipc_status AS detail, CAST(distinct_codes AS STRING) AS codes, CAST(patent_applications AS STRING) AS applications, '' AS introduced, '' AS deprecated
            FROM code_status
            UNION ALL
            SELECT 'Top Deprecated', ipc_class_symbol, CAST(patent_count AS STRING), '', introduced_date, deprecated_date
            FROM top_deprecated
        """,
        "sql_template": """
            WITH code_status AS (
                SELECT
                    CASE WHEN e.is_active IS TRUE THEN 'Active'
                         WHEN e.is_active IS FALSE THEN 'Deprecated'
                         ELSE 'Unknown (not in everused)'
                    END AS ipc_status,
                    COUNT(DISTINCT ipc.ipc_class_symbol) AS distinct_codes,
                    COUNT(DISTINCT ipc.appln_id) AS patent_applications
                FROM tls209_appln_ipc ipc
                JOIN tls201_appln a ON ipc.appln_id = a.appln_id
                LEFT JOIN tls_ipc_everused e ON ipc.ipc_class_symbol = e.symbol_patstat
                WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
                GROUP BY 1
            ),
            top_deprecated AS (
                SELECT
                    ipc.ipc_class_symbol,
                    e.introduced_date,
                    e.deprecated_date,
                    COUNT(DISTINCT ipc.appln_id) AS patent_count
                FROM tls209_appln_ipc ipc
                JOIN tls201_appln a ON ipc.appln_id = a.appln_id
                JOIN tls_ipc_everused e ON ipc.ipc_class_symbol = e.symbol_patstat
                WHERE a.appln_filing_year BETWEEN @year_start AND @year_end
                  AND e.is_active IS FALSE
                GROUP BY 1, 2, 3
                ORDER BY patent_count DESC
                LIMIT 20
            )
            SELECT 'Summary' AS result_type, ipc_status AS detail, CAST(distinct_codes AS STRING) AS codes, CAST(patent_applications AS STRING) AS applications, '' AS introduced, '' AS deprecated
            FROM code_status
            UNION ALL
            SELECT 'Top Deprecated', ipc_class_symbol, CAST(patent_count AS STRING), '', introduced_date, deprecated_date
            FROM top_deprecated
        """
    },
    "Q58": {
        "title": "What are all subclasses under an IPC or CPC class?",
        "tags": ["PATLIB"],
        "category": "Classification",
        "platforms": ["bigquery"],
        "description": "Browse the classification hierarchy tree - show all children of any IPC or CPC node",
        "parameters": {
            "parent_symbol": {
                "type": "text",
                "label": "Parent Symbol (e.g. A61B, H04L, Y02E)",
                "defaults": "A61B",
                "placeholder": "e.g., A61B, H04L, Y02E",
                "required": True
            },
            "system": {
                "type": "select",
                "label": "Classification System",
                "options": ["IPC", "CPC"],
                "defaults": "IPC",
                "required": True
            }
        },
        "explanation": """Expands the classification hierarchy tree below a given parent node, showing
all direct children and deeper descendants (up to 3 levels deep).

Uses a recursive query to traverse the parent-child relationships in the
IPC hierarchy (80,145 entries) or CPC hierarchy (254,249 entries).

The result is indented by depth level, making it easy to understand the
tree structure. Each entry shows the symbol, title, and hierarchy level.

Start with a subclass (e.g., A61B) to see its main groups, or with a
main group (e.g., A61B6/00) to see its subgroups.

Note: This query uses classification tables only available on BigQuery,
not on EPO TIP.""",
        "key_outputs": [
            "Classification symbols in tree order",
            "English titles at each level",
            "Depth relative to parent",
            "Kind (main group, subgroup level)"
        ],
        "estimated_seconds_first_run": 2,
        "estimated_seconds_cached": 1,
        "sql": """
            WITH RECURSIVE subtree AS (
                SELECT
                    symbol,
                    symbol_short,
                    title_en,
                    kind,
                    level,
                    0 AS depth
                FROM tls_ipc_hierarchy
                WHERE UPPER(symbol_short) = UPPER('A61B')

                UNION ALL

                SELECT
                    h.symbol,
                    h.symbol_short,
                    h.title_en,
                    h.kind,
                    h.level,
                    s.depth + 1
                FROM tls_ipc_hierarchy h
                JOIN subtree s ON h.parent = s.symbol
                WHERE s.depth < 3
            )
            SELECT
                depth,
                REPEAT('  ', depth) || symbol_short AS indented_symbol,
                symbol_short,
                title_en,
                kind,
                level
            FROM subtree
            ORDER BY symbol
            LIMIT 200
        """,
        "sql_template": """
            WITH RECURSIVE subtree AS (
                SELECT
                    symbol,
                    symbol_short,
                    title_en,
                    kind,
                    level,
                    0 AS depth
                FROM tls_ipc_hierarchy
                WHERE UPPER(symbol_short) = UPPER(@parent_symbol)

                UNION ALL

                SELECT
                    h.symbol,
                    h.symbol_short,
                    h.title_en,
                    h.kind,
                    h.level,
                    s.depth + 1
                FROM tls_ipc_hierarchy h
                JOIN subtree s ON h.parent = s.symbol
                WHERE s.depth < 3
            )
            SELECT
                depth,
                REPEAT('  ', depth) || symbol_short AS indented_symbol,
                symbol_short,
                title_en,
                kind,
                level
            FROM subtree
            ORDER BY symbol
            LIMIT 200
        """
    },
}

# =============================================================================
# DYNAMIC QUERIES - User-configurable parameters (DQ01 reference implementation)
# =============================================================================
# These queries have explicit parameter definitions for the UI.
# Regular QUERIES now also support sql_template for dynamic parameters.

DYNAMIC_QUERIES = {
    "DQ01": {
        "title": "Technology Trend Analysis",
        "tags": ["PATLIB", "BUSINESS", "UNIVERSITY"],
        "category": "Technology",
        "platforms": ["bigquery", "tip"],
        "description": "Analyze patent application trends by jurisdiction and technology field",
        "explanation": """Interactive analysis of patent filing trends over time.
Filter by filing jurisdiction (patent office), WIPO technology field, and year range.

Returns yearly application counts and unique invention counts (patent families).
Use this to identify technology trends, compare jurisdictions, or track sector growth.""",
        "key_outputs": [
            "Yearly application counts",
            "Unique inventions (patent families) per year",
            "Trend visualization"
        ],
        "estimated_seconds_first_run": 8,
        "estimated_seconds_cached": 2,
        "parameters": {
            "jurisdictions": {
                "type": "multiselect",
                "label": "Filing Jurisdictions",
                "description": "Patent offices where applications were filed (compare multiple)",
                "default": ["EP", "US", "CN"],
                "options_query": "JURISDICTIONS"
            },
            "tech_field": {
                "type": "select",
                "label": "Technology Field",
                "description": "WIPO technology field classification (35 fields)",
                "default": 13,
                "options_query": "TECH_FIELDS"
            },
            "year_range": {
                "type": "range",
                "label": "Filing Years",
                "description": "Range of filing years to analyze",
                "min": 2000,
                "max": 2024,
                "default": [2015, 2023]
            }
        },
        "sql_template": """
            SELECT
                a.appln_auth AS jurisdiction,
                a.appln_filing_year AS year,
                COUNT(DISTINCT a.appln_id) AS application_count,
                COUNT(DISTINCT a.docdb_family_id) AS invention_count
            FROM tls201_appln a
            JOIN tls230_appln_techn_field tf ON a.appln_id = tf.appln_id
            WHERE a.appln_auth IN UNNEST(@jurisdictions)
              AND tf.techn_field_nr = @tech_field
              AND a.appln_filing_year BETWEEN @year_start AND @year_end
              AND tf.weight > 0.5
            GROUP BY a.appln_auth, a.appln_filing_year
            ORDER BY a.appln_auth, a.appln_filing_year ASC
        """
    },
}

# =============================================================================
# REFERENCE DATA QUERIES - For populating dynamic query dropdowns
# =============================================================================

REFERENCE_QUERIES = {
    "JURISDICTIONS": """
        WITH jurisdiction_counts AS (
            SELECT
                a.appln_auth AS code,
                COALESCE(c.st3_name, a.appln_auth) AS name,
                COUNT(*) AS app_count
            FROM tls201_appln a
            LEFT JOIN tls801_country c ON a.appln_auth = c.ctry_code
            WHERE a.appln_auth IS NOT NULL
              AND a.appln_filing_year >= 2010
            GROUP BY a.appln_auth, c.st3_name
            HAVING COUNT(*) >= 1000
        )
        SELECT code, name
        FROM jurisdiction_counts
        ORDER BY app_count DESC
        LIMIT 50
    """,
    "TECH_FIELDS": """
        SELECT DISTINCT
            tf.techn_field_nr AS code,
            tf.techn_field AS name,
            tf.techn_sector AS sector
        FROM tls901_techn_field_ipc tf
        WHERE tf.techn_field_nr > 0
        ORDER BY tf.techn_sector, tf.techn_field_nr
    """
}
