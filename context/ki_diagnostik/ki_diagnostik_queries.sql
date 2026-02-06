-- =============================================================================
-- KI-gestützte Diagnostik: Patentanalyse für Fr. Spranger
-- PATSTAT BigQuery | Stand: 2026-02-05
-- Kontext: WIK-Papier Nr.535 + Hightech-Agenda Deutschland
-- =============================================================================
-- IPC-Strategie:
--   AI-Seite:        G06N (Neural Networks/ML) + G16H (Health Informatics)
--   Diagnostik-Seite: A61B 5/ (Messung), A61B 6/ (Bildgebung), A61B 8/ (Ultraschall)
--   Ausschlüsse:     A61B 34/ (Robotik), G01N (Labor), A61B 1/ (Endoskopie)
-- 
-- REGEXP löst Whitespace-Problem: '^A61B\s*5/' matcht "A61B 5/", "A61B  5/", "A61B5/"
-- =============================================================================


-- =============================================================================
-- QUERY A: Trend nach AI-Klasse und Diagnostik-Subklasse (FUNKTIONIERT ✅)
-- =============================================================================
-- Ergebnis: 20 Zeilen, G06N zeigt echten AI-Trend (15→56 bei A61B 5/, 2015-2018)
-- G16H dominiert volumenmäßig (265→351), ist aber breiter gefasst

WITH ai_diag AS (
  SELECT DISTINCT
    a.appln_id,
    a.appln_filing_year,
    a.appln_auth,
    CASE
      WHEN EXISTS (
        SELECT 1 FROM tls209_appln_ipc x 
        WHERE x.appln_id = a.appln_id 
          AND REGEXP_CONTAINS(x.ipc_class_symbol, r'^G06N')
      ) THEN 'G06N'
      ELSE 'G16H'
    END AS ai_class,
    CASE
      WHEN EXISTS (
        SELECT 1 FROM tls209_appln_ipc x 
        WHERE x.appln_id = a.appln_id 
          AND REGEXP_CONTAINS(x.ipc_class_symbol, r'^A61B\s*5/')
      ) THEN 'A61B 5/ (Messung/Diagnose)'
      WHEN EXISTS (
        SELECT 1 FROM tls209_appln_ipc x 
        WHERE x.appln_id = a.appln_id 
          AND REGEXP_CONTAINS(x.ipc_class_symbol, r'^A61B\s*6/')
      ) THEN 'A61B 6/ (Bildgebung)'
      WHEN EXISTS (
        SELECT 1 FROM tls209_appln_ipc x 
        WHERE x.appln_id = a.appln_id 
          AND REGEXP_CONTAINS(x.ipc_class_symbol, r'^A61B\s*8/')
      ) THEN 'A61B 8/ (Ultraschall)'
    END AS diag_class
  FROM tls201_appln a
  WHERE a.appln_auth IN ('DE', 'EP')
    AND a.appln_filing_year >= 2015
    AND (
      EXISTS (SELECT 1 FROM tls209_appln_ipc i1 
              WHERE i1.appln_id = a.appln_id 
                AND REGEXP_CONTAINS(i1.ipc_class_symbol, r'^G06N'))
      OR EXISTS (SELECT 1 FROM tls209_appln_ipc i2 
                 WHERE i2.appln_id = a.appln_id 
                   AND REGEXP_CONTAINS(i2.ipc_class_symbol, r'^G16H'))
    )
    AND EXISTS (
      SELECT 1 FROM tls209_appln_ipc i3 
      WHERE i3.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(i3.ipc_class_symbol, r'^A61B\s*(5|6|8)/')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex 
      WHERE ex.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex.ipc_class_symbol, r'^A61B\s*34/')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex2 
      WHERE ex2.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex2.ipc_class_symbol, r'^G01N')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex3 
      WHERE ex3.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex3.ipc_class_symbol, r'^A61B\s*1/')
    )
)

SELECT 
  appln_filing_year,
  ai_class,
  diag_class,
  COUNT(DISTINCT appln_id) AS applications
FROM ai_diag
WHERE diag_class IS NOT NULL
GROUP BY appln_filing_year, ai_class, diag_class
ORDER BY appln_filing_year, ai_class, diag_class;


-- =============================================================================
-- QUERY B: Top-Anmelder nach AI-Klasse und Diagnostik-Subklasse
-- =============================================================================
-- Erweiterung: Wer sind die Spieler? han_name für harmonisierte Namen.
-- applt_seq_nr > 0 = nur Anmelder (keine Erfinder)

WITH ai_diag AS (
  SELECT DISTINCT
    a.appln_id,
    a.appln_filing_year,
    a.appln_auth,
    CASE
      WHEN EXISTS (
        SELECT 1 FROM tls209_appln_ipc x 
        WHERE x.appln_id = a.appln_id 
          AND REGEXP_CONTAINS(x.ipc_class_symbol, r'^G06N')
      ) THEN 'G06N'
      ELSE 'G16H'
    END AS ai_class,
    CASE
      WHEN EXISTS (
        SELECT 1 FROM tls209_appln_ipc x 
        WHERE x.appln_id = a.appln_id 
          AND REGEXP_CONTAINS(x.ipc_class_symbol, r'^A61B\s*5/')
      ) THEN 'A61B 5/'
      WHEN EXISTS (
        SELECT 1 FROM tls209_appln_ipc x 
        WHERE x.appln_id = a.appln_id 
          AND REGEXP_CONTAINS(x.ipc_class_symbol, r'^A61B\s*6/')
      ) THEN 'A61B 6/'
      WHEN EXISTS (
        SELECT 1 FROM tls209_appln_ipc x 
        WHERE x.appln_id = a.appln_id 
          AND REGEXP_CONTAINS(x.ipc_class_symbol, r'^A61B\s*8/')
      ) THEN 'A61B 8/'
    END AS diag_class
  FROM tls201_appln a
  WHERE a.appln_auth IN ('DE', 'EP')
    AND a.appln_filing_year >= 2015
    AND (
      EXISTS (SELECT 1 FROM tls209_appln_ipc i1 
              WHERE i1.appln_id = a.appln_id 
                AND REGEXP_CONTAINS(i1.ipc_class_symbol, r'^G06N'))
      OR EXISTS (SELECT 1 FROM tls209_appln_ipc i2 
                 WHERE i2.appln_id = a.appln_id 
                   AND REGEXP_CONTAINS(i2.ipc_class_symbol, r'^G16H'))
    )
    AND EXISTS (
      SELECT 1 FROM tls209_appln_ipc i3 
      WHERE i3.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(i3.ipc_class_symbol, r'^A61B\s*(5|6|8)/')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex 
      WHERE ex.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex.ipc_class_symbol, r'^A61B\s*34/')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex2 
      WHERE ex2.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex2.ipc_class_symbol, r'^G01N')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex3 
      WHERE ex3.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex3.ipc_class_symbol, r'^A61B\s*1/')
    )
),

applicants AS (
  SELECT
    ad.appln_id,
    ad.appln_filing_year,
    ad.ai_class,
    ad.diag_class,
    COALESCE(p.han_name, p.person_name) AS applicant_name,
    p.person_ctry_code,
    p.psn_sector
  FROM ai_diag ad
  JOIN tls207_pers_appln pa ON ad.appln_id = pa.appln_id
  JOIN tls206_person p ON pa.person_id = p.person_id
  WHERE pa.applt_seq_nr > 0
    AND ad.diag_class IS NOT NULL
)

SELECT
  ai_class,
  diag_class,
  applicant_name,
  person_ctry_code AS country,
  psn_sector AS sector,
  COUNT(DISTINCT appln_id) AS patent_count,
  MIN(appln_filing_year) AS first_year,
  MAX(appln_filing_year) AS last_year
FROM applicants
GROUP BY ai_class, diag_class, applicant_name, person_ctry_code, psn_sector
HAVING COUNT(DISTINCT appln_id) >= 3
ORDER BY ai_class, diag_class, patent_count DESC;


-- =============================================================================
-- QUERY C: Top-20 Gesamtranking (über alle Klassen)
-- =============================================================================
-- Kompakte Übersicht: Wer hat die meisten KI-Diagnostik-Patente insgesamt?

WITH ai_diag AS (
  SELECT DISTINCT
    a.appln_id,
    a.appln_filing_year
  FROM tls201_appln a
  WHERE a.appln_auth IN ('DE', 'EP')
    AND a.appln_filing_year >= 2015
    AND (
      EXISTS (SELECT 1 FROM tls209_appln_ipc i1 
              WHERE i1.appln_id = a.appln_id 
                AND REGEXP_CONTAINS(i1.ipc_class_symbol, r'^G06N'))
      OR EXISTS (SELECT 1 FROM tls209_appln_ipc i2 
                 WHERE i2.appln_id = a.appln_id 
                   AND REGEXP_CONTAINS(i2.ipc_class_symbol, r'^G16H'))
    )
    AND EXISTS (
      SELECT 1 FROM tls209_appln_ipc i3 
      WHERE i3.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(i3.ipc_class_symbol, r'^A61B\s*(5|6|8)/')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex 
      WHERE ex.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex.ipc_class_symbol, r'^A61B\s*34/')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex2 
      WHERE ex2.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex2.ipc_class_symbol, r'^G01N')
    )
    AND NOT EXISTS (
      SELECT 1 FROM tls209_appln_ipc ex3 
      WHERE ex3.appln_id = a.appln_id 
        AND REGEXP_CONTAINS(ex3.ipc_class_symbol, r'^A61B\s*1/')
    )
)

SELECT
  COALESCE(p.han_name, p.person_name) AS applicant_name,
  p.person_ctry_code AS country,
  p.psn_sector AS sector,
  COUNT(DISTINCT ad.appln_id) AS total_patents,
  MIN(ad.appln_filing_year) AS first_year,
  MAX(ad.appln_filing_year) AS last_year,
  MAX(ad.appln_filing_year) - MIN(ad.appln_filing_year) AS active_years
FROM ai_diag ad
JOIN tls207_pers_appln pa ON ad.appln_id = pa.appln_id
JOIN tls206_person p ON pa.person_id = p.person_id
WHERE pa.applt_seq_nr > 0
GROUP BY COALESCE(p.han_name, p.person_name), p.person_ctry_code, p.psn_sector
HAVING COUNT(DISTINCT ad.appln_id) >= 5
ORDER BY total_patents DESC
LIMIT 20;
