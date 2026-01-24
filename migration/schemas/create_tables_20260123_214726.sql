-- EPO PATSTAT Table Schemas
-- Generated: 20260123_214726
-- Target project: patstat-mtc


-- tls201_appln
CREATE TABLE IF NOT EXISTS `patstat-mtc.patstat.tls201_appln` (
    appln_id INT64,
    appln_auth STRING,
    appln_nr STRING,
    appln_kind STRING,
    appln_filing_date DATE,
    appln_filing_year INT64,
    appln_nr_epodoc STRING,
    appln_nr_original STRING,
    ipr_type STRING,
    receiving_office STRING,
    internat_appln_id INT64,
    int_phase STRING,
    reg_phase STRING,
    nat_phase STRING,
    earliest_filing_date DATE,
    earliest_filing_year INT64,
    earliest_filing_id INT64,
    earliest_publn_date DATE,
    earliest_publn_year INT64,
    earliest_pat_publn_id INT64,
    granted STRING,
    docdb_family_id INT64,
    inpadoc_family_id INT64,
    docdb_family_size INT64,
    nb_citing_docdb_fam INT64,
    nb_applicants INT64,
    nb_inventors INT64
);

-- tls206_person
CREATE TABLE IF NOT EXISTS `patstat-mtc.patstat.tls206_person` (
    person_id INT64,
    person_name STRING,
    person_name_orig_lg STRING,
    person_address STRING,
    person_ctry_code STRING,
    nuts STRING,
    nuts_level INT64,
    doc_std_name_id INT64,
    doc_std_name STRING,
    psn_id INT64,
    psn_name STRING,
    psn_level INT64,
    psn_sector STRING,
    han_id INT64,
    han_name STRING,
    han_harmonized INT64,
    reg_code STRING
);

-- tls207_pers_appln
CREATE TABLE IF NOT EXISTS `patstat-mtc.patstat.tls207_pers_appln` (
    person_id INT64,
    appln_id INT64,
    applt_seq_nr INT64,
    invt_seq_nr INT64
);

-- tls209_appln_ipc
CREATE TABLE IF NOT EXISTS `patstat-mtc.patstat.tls209_appln_ipc` (
    appln_id INT64,
    ipc_class_symbol STRING,
    ipc_class_level STRING,
    ipc_version DATE,
    ipc_value STRING,
    ipc_position STRING,
    ipc_gener_auth STRING
);

-- tls211_pat_publn
CREATE TABLE IF NOT EXISTS `patstat-mtc.patstat.tls211_pat_publn` (
    pat_publn_id INT64,
    publn_auth STRING,
    publn_nr STRING,
    publn_nr_original STRING,
    publn_kind STRING,
    appln_id INT64,
    publn_date DATE,
    publn_lg STRING,
    publn_first_grant STRING,
    publn_claims INT64
);

-- tls212_citation
CREATE TABLE IF NOT EXISTS `patstat-mtc.patstat.tls212_citation` (
    pat_publn_id INT64,
    citn_replenished INT64,
    citn_id INT64,
    citn_origin STRING,
    cited_pat_publn_id INT64,
    cited_appln_id INT64,
    pat_citn_seq_nr INT64,
    cited_npl_publn_id STRING,
    npl_citn_seq_nr INT64,
    citn_gener_auth STRING
);

-- tls224_appln_cpc
CREATE TABLE IF NOT EXISTS `patstat-mtc.patstat.tls224_appln_cpc` (
    appln_id INT64,
    cpc_class_symbol STRING
);
