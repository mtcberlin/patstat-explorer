"""
PATSTAT Queries organized by Stakeholder.
Converted from BigQuery to PostgreSQL syntax.

Key conversions applied:
- CAST(x AS STRING) → x::TEXT
- DATE_DIFF(date1, date2, DAY) → (date1 - date2)
- FLOAT64 → DOUBLE PRECISION
- REGEXP_CONTAINS() → ~ (PostgreSQL regex)
- UNNEST([STRUCT(...)]) → VALUES clause
"""

QUERIES = {
    # =========================================================================
    # OVERVIEW / DATABASE EXPLORATION
    # =========================================================================
    "Overview": {
        "Database Tables": {
            "description": "List all tables in the PATSTAT database",
            "sql": """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
        },
        "Sample Patents (tls201_appln)": {
            "description": "Get a sample of 100 patents from tls201_appln",
            "sql": """
                SELECT *
                FROM tls201_appln
                LIMIT 100
            """
        },
    },

    # =========================================================================
    # STRATEGIC PLANNING / MARKET INTELLIGENCE
    # =========================================================================
    "Strategic Planning": {
        "Country Patent Activity and Grant Rates": {
            "description": """Which countries have the highest patent application activity since 2015,
and what are their grant rates? Identifies leading innovation hubs and their success rates.""",
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
            "description": """Patent activity in G7+China+Korea from 2015-2022 with green technology
(CPC Y02) percentage. Useful for ESG reporting and sustainability assessments.""",
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
            "description": """Most active technology fields (2018-2022) with family size and citation
impact. Reveals trending technology areas and their relative importance.""",
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
            "description": """AI-based enterprise resource planning (G06Q10 + G06N) landscape since 2018.
Shows yearly trends and top 10 applicants to monitor.""",
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
                    first_filing_date::TEXT AS first_filing,
                    latest_filing_date::TEXT AS latest_filing
                FROM top_applicants
                ORDER BY patent_count DESC
            """
        },
        "AI-Assisted Diagnostics Companies": {
            "description": """Companies building patent portfolios in AI-assisted diagnostics
(A61B + G06N intersection) with average time-to-grant.""",
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
                        (grant_date - appln_filing_date) AS days_to_grant
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
            "description": """Top patent applicants since 2010 with portfolio profile.
Identifies key players and their innovation activity over time.""",
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
            "description": """Where are B. Braun's main competitors filing their medical technology
patents geographically? Focus on EP, US, CN filings.""",
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
            "description": """Which patents were most frequently cited by applications filed in 2020?
Identifies influential prior art and citation patterns.""",
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
            "description": """Grant rates for diagnostic imaging patents (A61B 6/) at EPO vs USPTO vs CNIPA.
Helps inform international filing strategy.""",
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
            "description": """Which German Federal states show highest patent activity in A61B
(Diagnosis/Surgery) over the last 5 years?""",
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
            "description": """A61B patent activity by German federal state with per-capita comparison
(patents per million inhabitants).""",
            "sql": """
                WITH population_2023 AS (
                    SELECT * FROM (
                        VALUES
                        ('DE1', 'BADEN-WÜRTTEMBERG', 11280000),
                        ('DE2', 'BAYERN', 13370000),
                        ('DE3', 'BERLIN', 3850000),
                        ('DE4', 'BRANDENBURG', 2570000),
                        ('DE5', 'BREMEN', 680000),
                        ('DE6', 'HAMBURG', 1950000),
                        ('DE7', 'HESSEN', 6390000),
                        ('DE8', 'MECKLENBURG-VORPOMMERN', 1610000),
                        ('DE9', 'NIEDERSACHSEN', 8140000),
                        ('DEA', 'NORDRHEIN-WESTFALEN', 18140000),
                        ('DEB', 'RHEINLAND-PFALZ', 4160000),
                        ('DEC', 'SAARLAND', 990000),
                        ('DED', 'SACHSEN', 4090000),
                        ('DEE', 'SACHSEN-ANHALT', 2170000),
                        ('DEF', 'SCHLESWIG-HOLSTEIN', 2950000),
                        ('DEG', 'THÜRINGEN', 2110000)
                    ) AS t(nuts_code, bundesland, population)
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
            "description": """Compare Sachsen, Bayern, Baden-Württemberg patent activity
broken down by WIPO technology sectors.""",
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
                    ROUND(AVG(weight)::NUMERIC, 3) AS avg_tech_relevance_weight,
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
            "description": """Fastest-growing sub-classes within G06Q (IT methods for management)
in the last 3 years with top 3 applicants driving growth.""",
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
                            THEN (COUNT(CASE WHEN appln_filing_year = 2023 THEN 1 END)::DOUBLE PRECISION /
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
                    ROUND(da.growth_rate_pct::NUMERIC, 2) AS growth_rate_percent,
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
