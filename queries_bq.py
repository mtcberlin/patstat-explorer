"""
PATSTAT Queries organized by Stakeholder.
BigQuery syntax for EPO PATSTAT on Google BigQuery.

Key syntax differences from PostgreSQL:
- x::TEXT → CAST(x AS STRING)
- (date1 - date2) → DATE_DIFF(date1, date2, DAY)
- DOUBLE PRECISION → FLOAT64
- VALUES clause → UNNEST([STRUCT(...)])
- TO_CHAR() → FORMAT() or CAST()
- SUBSTR → SUBSTR (same)

Timing fields:
- estimated_seconds_first_run: Expected time for cold/uncached query execution
- estimated_seconds_cached: Expected time when BigQuery cache is warm (~0.3-0.5s typical)
"""

QUERIES = {
    # =========================================================================
    # OVERVIEW / DATABASE EXPLORATION
    # =========================================================================
    "Overview": {
        "Database Statistics": {
            "description": "Overall PATSTAT database statistics and key metrics",
            "explanation": """High-level statistics about the PATSTAT database:
- Total number of patent applications
- Date range of the data
- Number of unique applicants and inventors
- Geographic coverage (countries)

Essential for understanding the scope and coverage of the database.""",
            "key_outputs": [
                "Total patent applications",
                "Date range (earliest to latest)",
                "Unique applicants/inventors count",
                "Countries covered"
            ],
            "estimated_seconds_first_run": 1,
            "estimated_seconds_cached": 1,
            "sql": """
                SELECT 'Total Applications' AS metric, CAST(COUNT(*) AS STRING) AS value FROM `tls201_appln`
                UNION ALL
                SELECT 'Earliest Filing Year', CAST(MIN(appln_filing_year) AS STRING) FROM `tls201_appln` WHERE appln_filing_year > 0
                UNION ALL
                SELECT 'Latest Filing Year', CAST(MAX(appln_filing_year) AS STRING) FROM `tls201_appln`
                UNION ALL
                SELECT 'Granted Patents', CAST(COUNT(*) AS STRING) FROM `tls201_appln` WHERE granted = 'Y'
                UNION ALL
                SELECT 'Unique Persons', CAST(COUNT(*) AS STRING) FROM `tls206_person`
                UNION ALL
                SELECT 'Countries with Applicants', CAST(COUNT(DISTINCT person_ctry_code) AS STRING) FROM `tls206_person` WHERE person_ctry_code IS NOT NULL
            """
        },
        "Filing Authorities": {
            "description": "Patent offices (filing authorities) in the database with application counts",
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
            """
        },
        "Applications by Year": {
            "description": "Patent application trends over time (by filing year)",
            "explanation": """Shows the distribution of patent applications across filing years.
Useful for understanding data coverage and identifying trends in global patent activity.

Note: Recent years may show lower counts due to publication delays (18 months from filing).""",
            "key_outputs": [
                "Applications per year",
                "Year-over-year changes",
                "Grant rates per year"
            ],
            "estimated_seconds_first_run": 1,
            "estimated_seconds_cached": 1,
            "sql": """
                SELECT
                    appln_filing_year,
                    COUNT(*) AS applications,
                    COUNT(*) - LAG(COUNT(*)) OVER (ORDER BY appln_filing_year) AS yoy_change,
                    COUNT(CASE WHEN granted = 'Y' THEN 1 END) AS granted,
                    ROUND(COUNT(CASE WHEN granted = 'Y' THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS grant_rate_pct
                FROM tls201_appln
                WHERE appln_filing_year BETWEEN 1980 AND 2024
                GROUP BY appln_filing_year
                ORDER BY appln_filing_year DESC
            """
        },
        "Top IPC Classes": {
            "description": "Most common IPC technology classes in the database",
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
            """
        },
        "Sample Patents (tls201_appln)": {
            "description": "Sample of 100 patent applications with key fields",
            "explanation": """Returns a sample of patent applications to understand the data structure
and available fields in the main application table (tls201_appln).

This is the central table in PATSTAT - most queries start here.""",
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
            """
        },
    },

    # =========================================================================
    # STRATEGIC PLANNING / MARKET INTELLIGENCE
    # =========================================================================
    "Strategic Planning": {
        "Country Patent Activity and Grant Rates": {
            "description": "Which countries have the highest patent application activity since 2015, and what are their grant rates?",
            "explanation": """This query analyzes patent filing activity by applicant country since 2015,
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
            """
        },
        "Green Technology Trends by Country": {
            "description": "Patent activity in G7+China+Korea from 2015-2022 with green technology (CPC Y02) focus",
            "explanation": """This query tracks patent activity trends in the G7+China+Korea economies,
with a special focus on green/environmental technologies (CPC Y02 class).
The Y02 class covers climate change mitigation technologies, making this
useful for ESG reporting and sustainability assessments.

Tracks both total applications and the proportion dedicated to green tech.""",
            "key_outputs": [
                "Yearly patent trends by country",
                "Green technology patent counts (Y02 class)",
                "Green tech percentage (sustainability commitment indicator)"
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
            """
        },
    },

    # =========================================================================
    # TECHNOLOGY SCOUTING / R&D STRATEGY
    # =========================================================================
    "Technology Scouting": {
        "Most Active Technology Fields": {
            "description": "Most active technology fields (2018-2022) with family size and citation impact",
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
            "sql": """
                SELECT
                    tf.techn_sector,
                    tf.techn_field,
                    COUNT(DISTINCT a.appln_id) AS application_count,
                    AVG(a.docdb_family_size) AS avg_family_size,
                    AVG(a.nb_citing_docdb_fam) AS avg_citations
                FROM tls230_appln_techn_field atf
                JOIN tls901_techn_field_ipc tf ON atf.techn_field_nr = tf.techn_field_nr
                JOIN tls201_appln a ON atf.appln_id = a.appln_id
                WHERE a.appln_filing_year BETWEEN 2018 AND 2022
                  AND atf.weight > 0.5
                GROUP BY tf.techn_sector, tf.techn_field
                ORDER BY application_count DESC
                LIMIT 15
            """
        },
        "AI-based ERP Patent Landscape": {
            "description": "AI-based enterprise resource planning (G06Q10 + G06N) landscape since 2018",
            "explanation": """This query analyzes the patent landscape for AI-based ERP by identifying
applications with both G06Q10 (ERP/business methods) and G06N (AI/machine learning)
CPC classifications since 2018.

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
            """
        },
        "AI-Assisted Diagnostics Companies": {
            "description": "Companies building patent portfolios in AI-assisted diagnostics (A61B + G06N)",
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
            "estimated_seconds_first_run": 5,
            "estimated_seconds_cached": 1,
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
            """
        },
    },

    # =========================================================================
    # COMPETITIVE INTELLIGENCE
    # =========================================================================
    "Competitive Intelligence": {
        "Top Patent Applicants": {
            "description": "Top patent applicants since 2010 with portfolio profile",
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
            """
        },
        "Competitor Geographic Filing Strategy (MedTech)": {
            "description": "Where are B. Braun's main competitors filing their medical technology patents?",
            "explanation": """This query analyzes the geographic filing patterns of B. Braun's main competitors
in medical technology, focusing on EP (European Patent Office), US (USPTO), and
CN (CNIPA) filings.

Uses WIPO technology sector classification (Instruments) instead of direct IPC patterns.
Competitor list includes: Medtronic, Johnson & Johnson, Abbott, Boston Scientific,
Stryker, Zimmer, Smith & Nephew, Edwards, Baxter, Fresenius, and B. Braun itself.""",
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
            """
        },
    },

    # =========================================================================
    # PATENT PROSECUTION / IP MANAGEMENT
    # =========================================================================
    "Patent Prosecution": {
        "Most Cited Patents (2020)": {
            "description": "Which patents were most frequently cited by applications filed in 2020?",
            "explanation": """This query builds a citation network to identify the most influential prior
art patents. By focusing on 2020 citing applications, it shows which older
patents remain technically relevant. The citation lag metric reveals how
quickly innovations become foundational knowledge in the field.

Minimum threshold of 10 citations ensures significance.""",
            "key_outputs": [
                "Most cited patents (influence indicator)",
                "Citation lag in years (knowledge diffusion speed)",
                "Cited patent filing year"
            ],
            "estimated_seconds_first_run": 10,
            "estimated_seconds_cached": 1,
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
            """
        },
        "Diagnostic Imaging Grant Rates by Office": {
            "description": "Grant rates for diagnostic imaging patents (A61B 6/) at EPO vs USPTO vs CNIPA",
            "explanation": """This query analyzes grant rates for diagnostic imaging patents (IPC subclass A61B 6/)
across three major patent offices. A61B 6/ covers diagnostic imaging technologies
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
            """
        },
    },

    # =========================================================================
    # REGIONAL PATLIB / ECONOMIC DEVELOPMENT
    # =========================================================================
    "Regional Analysis (Germany)": {
        "German Federal States - Medical Tech (A61B)": {
            "description": "Which German Federal states show highest patent activity in A61B (Diagnosis/Surgery)?",
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
            """
        },
        "German Federal States - Per Capita Analysis": {
            "description": "A61B patent activity by German federal state with per-capita comparison",
            "explanation": """This query analyzes patent activity in IPC class A61B (medical diagnosis/surgery)
over the last 5 years, focusing on German federal states with per-capita comparison.

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
            """
        },
        "Regional Comparison by Tech Sector": {
            "description": "Compare Sachsen, Bayern, Baden-Württemberg patent activity by WIPO technology sectors",
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
            "sql": """
                WITH regional_patents AS (
                    SELECT
                        a.appln_id,
                        a.appln_filing_year,
                        p.nuts,
                        n.nuts_label,
                        CASE
                            WHEN LOWER(n.nuts_label) LIKE '%sachsen%' OR LOWER(n.nuts_label) LIKE '%saxony%' THEN 'Sachsen'
                            WHEN LOWER(n.nuts_label) LIKE '%bayern%' OR LOWER(n.nuts_label) LIKE '%bavaria%' THEN 'Bayern'
                            WHEN LOWER(n.nuts_label) LIKE '%baden%württemberg%' OR LOWER(n.nuts_label) LIKE '%baden-württemberg%' THEN 'Baden-Württemberg'
                            ELSE 'Other'
                        END AS region_group
                    FROM tls201_appln a
                    JOIN tls207_pers_appln pa ON a.appln_id = pa.appln_id
                    JOIN tls206_person p ON pa.person_id = p.person_id
                    JOIN tls904_nuts n ON p.nuts = n.nuts
                    WHERE pa.applt_seq_nr > 0
                      AND a.appln_filing_year >= 2010
                      AND n.nuts_level = 1
                      AND (LOWER(n.nuts_label) LIKE '%sachsen%' OR LOWER(n.nuts_label) LIKE '%saxony%'
                           OR LOWER(n.nuts_label) LIKE '%bayern%' OR LOWER(n.nuts_label) LIKE '%bavaria%'
                           OR LOWER(n.nuts_label) LIKE '%baden%württemberg%' OR LOWER(n.nuts_label) LIKE '%baden-württemberg%')
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
                    WHERE rp.region_group != 'Other'
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
            """
        },
    },

    # =========================================================================
    # TECHNOLOGY TRANSFER / INNOVATION SCOUTING
    # =========================================================================
    "Technology Transfer": {
        "Fastest-Growing G06Q Subclasses": {
            "description": "Fastest-growing sub-classes within G06Q (IT methods for management) in 3 years",
            "explanation": """This query identifies the fastest-growing G06Q sub-classes by comparing
filing activity between the base year (2021) and the most recent year (2023).
It also identifies the top 3 applicants driving growth in each subclass.

G06Q covers IT methods for management, administration, commerce, etc.
Uses SUBSTR to extract subclass - handles variable whitespace correctly.""",
            "key_outputs": [
                "Fastest-growing G06Q subclasses by growth rate",
                "Year-over-year comparison (2021 vs 2023)",
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
            """
        },
    },
}
