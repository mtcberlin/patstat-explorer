/*
download from https://publication-bdds.apps.epo.org/raw-data/products/subscription/product/17
have a user with pg_read_server_files granted connected to a DB 
*/

DROP TABLE IF EXISTS tls201_appln;
CREATE TABLE tls201_appln (
    appln_id integer DEFAULT 0 NOT NULL,
    appln_auth char(2) DEFAULT '' NOT NULL,
    appln_nr varchar(15) DEFAULT '' NOT NULL,
    appln_kind char(2) DEFAULT '' NOT NULL,
    appln_filing_date date DEFAULT '9999-12-31' NOT NULL,
    appln_filing_year smallint DEFAULT '9999' NOT NULL,
    appln_nr_epodoc varchar(20) DEFAULT '' NOT NULL,
    appln_nr_original varchar(100) DEFAULT '' NOT NULL,
    ipr_type char(2) DEFAULT '' NOT NULL,
    receiving_office char(2) DEFAULT '' NOT NULL,
    internat_appln_id integer DEFAULT 0 NOT NULL,
    int_phase char(1) DEFAULT 'N' NOT NULL,
    reg_phase char(1) DEFAULT 'N' NOT NULL,
    nat_phase char(1) DEFAULT 'N' NOT NULL,
    earliest_filing_date date DEFAULT '9999-12-31' NOT NULL,
    earliest_filing_year smallint DEFAULT '9999' NOT NULL,
    earliest_filing_id integer DEFAULT 0 NOT NULL,
    earliest_publn_date date DEFAULT '9999-12-31' NOT NULL,
    earliest_publn_year smallint DEFAULT 9999 NOT NULL,
    earliest_pat_publn_id integer DEFAULT 0 NOT NULL,
    granted char(1) DEFAULT 'N' NOT NULL,
    docdb_family_id integer DEFAULT 0 NOT NULL,
    inpadoc_family_id integer DEFAULT 0 NOT NULL,
    docdb_family_size smallint DEFAULT 0 NOT NULL,
    nb_citing_docdb_fam smallint DEFAULT 0 NOT NULL,
    nb_applicants smallint DEFAULT 0 NOT NULL,
    nb_inventors smallint DEFAULT 0 NOT NULL
);
copy tls201_appln (appln_id,appln_auth,appln_nr,appln_kind,appln_filing_date,appln_filing_year,appln_nr_epodoc,appln_nr_original,ipr_type,receiving_office,internat_appln_id,int_phase,reg_phase,nat_phase,earliest_filing_date,earliest_filing_year,earliest_filing_id,earliest_publn_date,earliest_publn_year,earliest_pat_publn_id,granted,docdb_family_id,inpadoc_family_id,docdb_family_size,nb_citing_docdb_fam,nb_applicants,nb_inventors) from '/tmp/tls201_appln_part01.csv' CSV header;
copy tls201_appln (appln_id,appln_auth,appln_nr,appln_kind,appln_filing_date,appln_filing_year,appln_nr_epodoc,appln_nr_original,ipr_type,receiving_office,internat_appln_id,int_phase,reg_phase,nat_phase,earliest_filing_date,earliest_filing_year,earliest_filing_id,earliest_publn_date,earliest_publn_year,earliest_pat_publn_id,granted,docdb_family_id,inpadoc_family_id,docdb_family_size,nb_citing_docdb_fam,nb_applicants,nb_inventors) from '/tmp/tls201_appln_part02.csv' CSV header;
copy tls201_appln (appln_id,appln_auth,appln_nr,appln_kind,appln_filing_date,appln_filing_year,appln_nr_epodoc,appln_nr_original,ipr_type,receiving_office,internat_appln_id,int_phase,reg_phase,nat_phase,earliest_filing_date,earliest_filing_year,earliest_filing_id,earliest_publn_date,earliest_publn_year,earliest_pat_publn_id,granted,docdb_family_id,inpadoc_family_id,docdb_family_size,nb_citing_docdb_fam,nb_applicants,nb_inventors) from '/tmp/tls201_appln_part03.csv' CSV header;
ALTER TABLE tls201_appln ADD PRIMARY KEY (appln_id);
CREATE INDEX ON tls201_appln (appln_auth, appln_nr, appln_kind, receiving_office);
select count(*) from tls201_appln -- > 140525582
-- tls201_appln count: 140525582


DROP TABLE IF EXISTS tls202_appln_title;
CREATE TABLE tls202_appln_title (
    appln_id integer DEFAULT 0 NOT NULL,
    appln_title_lg char(2) DEFAULT '' NOT NULL,
    appln_title text NOT NULL
);
copy tls202_appln_title (appln_id,appln_title_lg,appln_title) from '/tmp/tls202_appln_title_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls202_appln_title ADD PRIMARY KEY (appln_id);
select count(*) from tls202_appln_title -- > 119259497
-- tls202_appln_title count: 119259497


DROP TABLE IF EXISTS tls203_appln_abstr;
CREATE TABLE tls203_appln_abstr (
    appln_id integer DEFAULT 0 NOT NULL,
    appln_abstract_lg char(2) DEFAULT '' NOT NULL,
    appln_abstract text DEFAULT '' NOT NULL
);
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part01.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part02.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part03.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part04.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part05.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part06.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part07.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part08.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part09.csv' CSV header ENCODING 'UTF8';
copy tls203_appln_abstr (appln_id,appln_abstract_lg,appln_abstract) from '/tmp/tls203_appln_abstr_part10.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls203_appln_abstr ADD PRIMARY KEY (appln_id);
select count(*) from tls203_appln_abstr -- > 96536721
-- tls203_appln_abstr count: 96536721


DROP TABLE IF EXISTS tls204_appln_prior;
CREATE TABLE tls204_appln_prior (
    appln_id integer DEFAULT 0 NOT NULL,
    prior_appln_id integer DEFAULT 0 NOT NULL,
    prior_appln_seq_nr smallint DEFAULT 0 NOT NULL
);
copy tls204_appln_prior(appln_id,prior_appln_id,prior_appln_seq_nr) from '/tmp/tls204_appln_prior_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls204_appln_prior ADD PRIMARY KEY (appln_id, prior_appln_id);
select count(*) from tls204_appln_prior -- > 53194773
-- tls204_appln_prior count: 53194773


DROP TABLE IF EXISTS tls205_tech_rel;
CREATE TABLE tls205_tech_rel (
    appln_id integer DEFAULT 0 NOT NULL,
    tech_rel_appln_id integer DEFAULT 0 NOT NULL
);
copy tls205_tech_rel(appln_id,tech_rel_appln_id) from '/tmp/tls205_tech_rel_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls205_tech_rel ADD PRIMARY KEY (appln_id, tech_rel_appln_id);
select count(*) from tls205_tech_rel -- > 4160592
-- tls205_tech_rel count: 4160592


DROP TABLE IF EXISTS tls206_person;
CREATE TABLE tls206_person (
    person_id integer DEFAULT 0 NOT NULL,
    person_name text DEFAULT '' NOT NULL,
    person_name_orig_lg text DEFAULT '' NOT NULL,
    person_address text DEFAULT '' NOT NULL,
    person_ctry_code char(2) DEFAULT '' NOT NULL,
    nuts varchar(5) DEFAULT '' NOT NULL,
    nuts_level smallint DEFAULT 9 NOT NULL,
    doc_std_name_id integer DEFAULT 0 NOT NULL,
    doc_std_name text DEFAULT '' NOT NULL,
    psn_id integer DEFAULT 0 NOT NULL,
    psn_name text DEFAULT '' NOT NULL,
    psn_level smallint DEFAULT 0 NOT NULL,
    psn_sector varchar(50) DEFAULT '' NOT NULL,
    han_id integer DEFAULT 0 NOT NULL,
    han_name text DEFAULT '' NOT NULL,
    han_harmonized integer DEFAULT 0 NOT NULL
);
copy tls206_person(person_id,person_name,person_name_orig_lg,person_address,person_ctry_code,nuts,nuts_level,doc_std_name_id,doc_std_name,psn_id,psn_name,psn_level,psn_sector,han_id,han_name,han_harmonized) from '/tmp/tls206_person_part01.csv' CSV header ENCODING 'UTF8';
copy tls206_person(person_id,person_name,person_name_orig_lg,person_address,person_ctry_code,nuts,nuts_level,doc_std_name_id,doc_std_name,psn_id,psn_name,psn_level,psn_sector,han_id,han_name,han_harmonized) from '/tmp/tls206_person_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls206_person ADD PRIMARY KEY (person_id);
CREATE INDEX idx_person_composite ON tls206_person (person_id, nuts) WHERE person_address <> '' OR person_ctry_code <> '' OR nuts <> '';
select count(*) from tls206_person -- > 97853865
-- tls206_person count: 97853865


DROP TABLE IF EXISTS tls207_pers_appln;
CREATE TABLE tls207_pers_appln (
    person_id integer DEFAULT 0 NOT NULL,
    appln_id integer DEFAULT 0 NOT NULL,
    applt_seq_nr smallint DEFAULT 0 NOT NULL,
    invt_seq_nr smallint DEFAULT 0 NOT NULL
);
copy tls207_pers_appln(person_id,appln_id,applt_seq_nr,invt_seq_nr) from '/tmp/tls207_pers_appln_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls207_pers_appln ADD PRIMARY KEY (person_id, appln_id, applt_seq_nr, invt_seq_nr);
CREATE INDEX idx_pers_appln_composite ON tls207_pers_appln (appln_id, person_id, invt_seq_nr);
select count(*) from tls207_pers_appln -- > 408478469
-- tls207_pers_appln count: 408478469


DROP TABLE IF EXISTS tls209_appln_ipc;
CREATE TABLE tls209_appln_ipc (
    appln_id integer DEFAULT 0 NOT NULL,
    ipc_class_symbol varchar(15) DEFAULT '' NOT NULL,
    ipc_class_level char(1) DEFAULT '' NOT NULL,
    ipc_version date DEFAULT '9999-12-31' NOT NULL,
    ipc_value char(1) DEFAULT '' NOT NULL,
    ipc_position char(1) DEFAULT '' NOT NULL,
    ipc_gener_auth char(2) DEFAULT '' NOT NULL
);
copy tls209_appln_ipc(appln_id,ipc_class_symbol,ipc_class_level,ipc_version,ipc_value,ipc_position,ipc_gener_auth) from '/tmp/tls209_appln_ipc_part01.csv' CSV header ENCODING 'UTF8';
copy tls209_appln_ipc(appln_id,ipc_class_symbol,ipc_class_level,ipc_version,ipc_value,ipc_position,ipc_gener_auth) from '/tmp/tls209_appln_ipc_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls209_appln_ipc ADD PRIMARY KEY (appln_id, ipc_class_symbol);
CREATE INDEX idx_appln_ipc_class_symbol ON tls209_appln_ipc (appln_id, ipc_class_symbol);
CREATE INDEX idx_appln_ipc_substring ON tls209_appln_ipc (appln_id, (substring(ipc_class_symbol, 1, 4)));
select count(*) from tls209_appln_ipc -- > 374559946
-- tls209_appln_ipc count: 374559946


DROP TABLE IF EXISTS tls210_appln_n_cls;
CREATE TABLE tls210_appln_n_cls (
    appln_id integer DEFAULT 0 NOT NULL,
    nat_class_symbol varchar(15) DEFAULT '' NOT NULL
);
copy tls210_appln_n_cls(appln_id,nat_class_symbol) from '/tmp/tls210_appln_n_cls_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls210_appln_n_cls ADD PRIMARY KEY (appln_id, nat_class_symbol);
select count(*) from tls210_appln_n_cls -- > 26217769
-- tls210_appln_n_cls count: 26217769


DROP TABLE IF EXISTS tls211_pat_publn;
CREATE TABLE tls211_pat_publn (
    pat_publn_id integer DEFAULT 0 NOT NULL,
    publn_auth char(2) DEFAULT '' NOT NULL,
    publn_nr varchar(15) DEFAULT '' NOT NULL,
    publn_nr_original varchar(100) DEFAULT '' NOT NULL,
    publn_kind char(2) DEFAULT '' NOT NULL,
    appln_id integer,
    publn_date date DEFAULT '9999-12-31' NOT NULL,
    publn_lg char(2) DEFAULT '' NOT NULL,
    publn_first_grant char(1) DEFAULT '' NOT NULL,
    publn_claims integer DEFAULT 0 NOT NULL
);
copy tls211_pat_publn(pat_publn_id,publn_auth,publn_nr,publn_nr_original,publn_kind,appln_id,publn_date,publn_lg,publn_first_grant,publn_claims) from '/tmp/tls211_pat_publn_part01.csv' CSV header ENCODING 'UTF8';
copy tls211_pat_publn(pat_publn_id,publn_auth,publn_nr,publn_nr_original,publn_kind,appln_id,publn_date,publn_lg,publn_first_grant,publn_claims) from '/tmp/tls211_pat_publn_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls211_pat_publn ADD PRIMARY KEY (pat_publn_id);
select count(*) from tls211_pat_publn -- > 167837244
-- tls211_pat_publn count: 167837244


DROP TABLE IF EXISTS tls212_citation;
CREATE TABLE tls212_citation (
    pat_publn_id integer DEFAULT 0 NOT NULL,
    citn_replenished integer DEFAULT 0 NOT NULL,
    citn_id smallint DEFAULT 0 NOT NULL,
    citn_origin char(3) DEFAULT '' NOT NULL,
    cited_pat_publn_id integer DEFAULT 0 NOT NULL,
    cited_appln_id integer DEFAULT 0 NOT NULL,
    pat_citn_seq_nr smallint DEFAULT 0::smallint NOT NULL,
    cited_npl_publn_id varchar(32) DEFAULT '0' NOT NULL,
    npl_citn_seq_nr smallint DEFAULT 0 NOT NULL,
    citn_gener_auth char(2) DEFAULT '' NOT NULL
);
copy tls212_citation(pat_publn_id,citn_replenished,citn_id,citn_origin,cited_pat_publn_id,cited_appln_id,pat_citn_seq_nr,cited_npl_publn_id,npl_citn_seq_nr,citn_gener_auth) from '/tmp/tls212_citation_part01.csv' CSV header ENCODING 'UTF8';
copy tls212_citation(pat_publn_id,citn_replenished,citn_id,citn_origin,cited_pat_publn_id,cited_appln_id,pat_citn_seq_nr,cited_npl_publn_id,npl_citn_seq_nr,citn_gener_auth) from '/tmp/tls212_citation_part02.csv' CSV header ENCODING 'UTF8';
copy tls212_citation(pat_publn_id,citn_replenished,citn_id,citn_origin,cited_pat_publn_id,cited_appln_id,pat_citn_seq_nr,cited_npl_publn_id,npl_citn_seq_nr,citn_gener_auth) from '/tmp/tls212_citation_part03.csv' CSV header ENCODING 'UTF8';
copy tls212_citation(pat_publn_id,citn_replenished,citn_id,citn_origin,cited_pat_publn_id,cited_appln_id,pat_citn_seq_nr,cited_npl_publn_id,npl_citn_seq_nr,citn_gener_auth) from '/tmp/tls212_citation_part04.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls212_citation ADD PRIMARY KEY (pat_publn_id, citn_replenished, citn_id);
select count(*) from tls212_citation -- > 596775557
-- tls212_citation count: 596775557


DROP TABLE IF EXISTS tls214_npl_publn;
CREATE TABLE tls214_npl_publn (
    npl_publn_id varchar(32) DEFAULT '0' NOT NULL,
    xp_nr integer DEFAULT 0 NOT NULL,
    npl_type char(1) DEFAULT '' NOT NULL,
    npl_biblio text DEFAULT '' NOT NULL,
    npl_author varchar(2000) DEFAULT '' NOT NULL,
    npl_title1 text DEFAULT '' NOT NULL,
    npl_title2 varchar(1000) DEFAULT '' NOT NULL,
    npl_editor varchar(500) DEFAULT '' NOT NULL,
    npl_volume varchar(100) DEFAULT '' NOT NULL,
    npl_issue varchar(100) DEFAULT '' NOT NULL,
    npl_publn_date varchar(8) DEFAULT '' NOT NULL,
    npl_publn_end_date varchar(8) DEFAULT '' NOT NULL,
    npl_publisher varchar(500) DEFAULT '' NOT NULL,
    npl_page_first varchar(200) DEFAULT '' NOT NULL,
    npl_page_last varchar(200) DEFAULT '' NOT NULL,
    npl_abstract_nr varchar(100) DEFAULT '' NOT NULL,
    npl_doi varchar(500) DEFAULT '' NOT NULL,
    npl_isbn varchar(30) DEFAULT '' NOT NULL,
    npl_issn varchar(30) DEFAULT '' NOT NULL,
    online_availability varchar(1000) DEFAULT '' NOT NULL,
    online_classification varchar(35) DEFAULT '' NOT NULL,
    online_search_date varchar(8) DEFAULT '' NOT NULL
);
copy tls214_npl_publn(npl_publn_id,xp_nr,npl_type,npl_biblio,npl_author,npl_title1,npl_title2,npl_editor,npl_volume,npl_issue,npl_publn_date,npl_publn_end_date,npl_publisher,npl_page_first,npl_page_last,npl_abstract_nr,npl_doi,npl_isbn,npl_issn,online_availability,online_classification,online_search_date) from '/tmp/tls214_npl_publn_part01.csv' CSV header ENCODING 'UTF8';
-- iconv -c -t utf8 tls214_npl_publn_part02.broken.csv >tls214_npl_publn_part02.csv
copy tls214_npl_publn(npl_publn_id,xp_nr,npl_type,npl_biblio,npl_author,npl_title1,npl_title2,npl_editor,npl_volume,npl_issue,npl_publn_date,npl_publn_end_date,npl_publisher,npl_page_first,npl_page_last,npl_abstract_nr,npl_doi,npl_isbn,npl_issn,online_availability,online_classification,online_search_date) from '/tmp/tls214_npl_publn_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls214_npl_publn ADD PRIMARY KEY (npl_publn_id);
select count(*) from tls214_npl_publn -- > 43569746
-- tls214_npl_publn count: 43569746


DROP TABLE IF EXISTS tls215_citn_categ;
CREATE TABLE tls215_citn_categ (
    pat_publn_id integer DEFAULT 0 NOT NULL,
    citn_replenished integer DEFAULT 0 NOT NULL,
    citn_id smallint DEFAULT 0 NOT NULL,
    citn_categ varchar(10) DEFAULT '' NOT NULL,
    relevant_claim smallint DEFAULT 0 NOT NULL
);
-- sed -i.bak 's/\r$//g' tls215_citn_categ_part01.csv
copy tls215_citn_categ(pat_publn_id,citn_replenished,citn_id,citn_categ,relevant_claim) from '/tmp/tls215_citn_categ_part01.csv' CSV header ENCODING 'UTF8';
-- sed -i.bak 's/\r$//g' tls215_citn_categ_part02.csv
copy tls215_citn_categ(pat_publn_id,citn_replenished,citn_id,citn_categ,relevant_claim) from '/tmp/tls215_citn_categ_part02.csv' CSV header ENCODING 'UTF8';
-- sed -i.bak 's/\r$//g' tls215_citn_categ_part03.csv
copy tls215_citn_categ(pat_publn_id,citn_replenished,citn_id,citn_categ,relevant_claim) from '/tmp/tls215_citn_categ_part03.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls215_citn_categ ADD PRIMARY KEY (pat_publn_id, citn_replenished, citn_id, citn_categ, relevant_claim);
select count(*) from tls215_citn_categ -- > 1346861951
-- tls215_citn_categ count: 1346861951


DROP TABLE IF EXISTS tls216_appln_contn;
CREATE TABLE tls216_appln_contn (
    appln_id integer DEFAULT 0 NOT NULL,
    parent_appln_id integer DEFAULT 0 NOT NULL,
    contn_type char(3) DEFAULT '' NOT NULL
);
copy tls216_appln_contn(appln_id,parent_appln_id,contn_type) from '/tmp/tls216_appln_contn_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls216_appln_contn ADD PRIMARY KEY (appln_id, parent_appln_id);
select count(*) from tls216_appln_contn; -- > 5819586
-- tls216_appln_contn count: 5819586


DROP TABLE IF EXISTS tls222_appln_jp_class;
CREATE TABLE tls222_appln_jp_class (
    appln_id integer DEFAULT 0 NOT NULL,
    jp_class_scheme varchar(5) DEFAULT '' NOT NULL,
    jp_class_symbol varchar(50) DEFAULT '' NOT NULL
);
copy tls222_appln_jp_class(appln_id,jp_class_scheme,jp_class_symbol) from '/tmp/tls222_appln_jp_class_part01.csv' CSV header ENCODING 'UTF8';
copy tls222_appln_jp_class(appln_id,jp_class_scheme,jp_class_symbol) from '/tmp/tls222_appln_jp_class_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls222_appln_jp_class ADD PRIMARY KEY (appln_id, jp_class_scheme, jp_class_symbol);
select count(*) from tls222_appln_jp_class -- > 428299335
-- tls222_appln_jp_class count: 428299335


DROP TABLE IF EXISTS tls224_appln_cpc;
CREATE TABLE tls224_appln_cpc (
    appln_id integer DEFAULT 0 NOT NULL,
    cpc_class_symbol varchar(19) DEFAULT '' NOT NULL
);
copy tls224_appln_cpc(appln_id,cpc_class_symbol) from '/tmp/tls224_appln_cpc_part01.csv' CSV header ENCODING 'UTF8';
copy tls224_appln_cpc(appln_id,cpc_class_symbol) from '/tmp/tls224_appln_cpc_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls224_appln_cpc ADD PRIMARY KEY (appln_id, cpc_class_symbol);
select count(*) from tls224_appln_cpc; -- > 436450350
-- tls224_appln_cpc count: 436450350


DROP TABLE IF EXISTS tls225_docdb_fam_cpc;
CREATE TABLE tls225_docdb_fam_cpc (
    docdb_family_id integer DEFAULT 0 NOT NULL,
    cpc_class_symbol varchar(19) DEFAULT '' NOT NULL,
    cpc_gener_auth varchar(2) DEFAULT '' NOT NULL,
    cpc_version date DEFAULT '9999-12-31' NOT NULL,
    cpc_position char(1) DEFAULT '' NOT NULL,
    cpc_value char(1) DEFAULT '' NOT NULL,
    cpc_action_date date DEFAULT '9999-12-31' NOT NULL,
    cpc_status char(1) DEFAULT '' NOT NULL,
    cpc_data_source char(1) DEFAULT '' NOT NULL
);
copy tls225_docdb_fam_cpc(docdb_family_id,cpc_class_symbol,cpc_gener_auth,cpc_version,cpc_position,cpc_value,cpc_action_date,cpc_status,cpc_data_source) from '/tmp/tls225_docdb_fam_cpc_part01.csv' CSV header ENCODING 'UTF8';
copy tls225_docdb_fam_cpc(docdb_family_id,cpc_class_symbol,cpc_gener_auth,cpc_version,cpc_position,cpc_value,cpc_action_date,cpc_status,cpc_data_source) from '/tmp/tls225_docdb_fam_cpc_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls225_docdb_fam_cpc ADD PRIMARY KEY (docdb_family_id, cpc_class_symbol, cpc_gener_auth);
select count(*) from tls225_docdb_fam_cpc -- > 224464483
--tls225_docdb_fam_cpc count: 224464483


DROP TABLE IF EXISTS tls226_person_orig;
CREATE TABLE tls226_person_orig (
	person_orig_id integer DEFAULT 0 NOT NULL,
	person_id integer DEFAULT 0 NOT NULL,
	source char(5) DEFAULT '' NOT NULL,
	source_version varchar(10) DEFAULT '' NOT NULL,
	name_freeform varchar(1000) DEFAULT '' NOT NULL,
	person_name_orig_lg varchar(1000) DEFAULT '' NOT NULL,
	last_name varchar(500) DEFAULT '' NOT NULL,
	first_name varchar(500) DEFAULT '' NOT NULL,
	middle_name varchar(500) DEFAULT '' NOT NULL,
	address_freeform varchar(1000) DEFAULT '' NOT NULL,
	address_1 varchar(500) DEFAULT '' NOT NULL,
	address_2 varchar(500) DEFAULT '' NOT NULL,
	address_3 varchar(500) DEFAULT '' NOT NULL,
	address_4 varchar(500) DEFAULT '' NOT NULL,
	address_5 varchar(500) DEFAULT '' NOT NULL,
	street varchar(500) DEFAULT '' NOT NULL,
	city varchar(200) DEFAULT '' NOT NULL,
  	zip_code varchar(30) DEFAULT '' NOT NULL,
	state char(2) DEFAULT '' NOT NULL,
	person_ctry_code char(2) DEFAULT '' NOT NULL,
	residence_ctry_code char(2) DEFAULT '' NOT NULL,
	role varchar(2) DEFAULT '' NOT NULL
);
copy tls226_person_orig(person_orig_id,person_id,source,source_version,name_freeform,person_name_orig_lg,last_name,first_name,middle_name,address_freeform,address_1,address_2,address_3,address_4,address_5,street,city,zip_code,state,person_ctry_code,residence_ctry_code,role) from '/tmp/tls226_person_orig_part01.csv' CSV header ENCODING 'UTF8';
copy tls226_person_orig(person_orig_id,person_id,source,source_version,name_freeform,person_name_orig_lg,last_name,first_name,middle_name,address_freeform,address_1,address_2,address_3,address_4,address_5,street,city,zip_code,state,person_ctry_code,residence_ctry_code,role) from '/tmp/tls226_person_orig_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls226_person_orig ADD PRIMARY KEY (person_orig_id);
select count(*) from tls226_person_orig; -- >  120640365
-- tls226_person_orig count: 120640365


DROP TABLE IF EXISTS tls227_pers_publn;
CREATE TABLE tls227_pers_publn (
    person_id integer DEFAULT 0 NOT NULL,
    pat_publn_id integer DEFAULT 0 NOT NULL,
    applt_seq_nr integer DEFAULT 0 NOT NULL,
    invt_seq_nr integer DEFAULT 0 NOT NULL
);
copy tls227_pers_publn(person_id,pat_publn_id,applt_seq_nr,invt_seq_nr) from '/tmp/tls227_pers_publn_part01.csv' CSV header ENCODING 'UTF8';
copy tls227_pers_publn(person_id,pat_publn_id,applt_seq_nr,invt_seq_nr) from '/tmp/tls227_pers_publn_part02.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls227_pers_publn ADD PRIMARY KEY (person_id, pat_publn_id, applt_seq_nr, invt_seq_nr);
select count(*) from tls227_pers_publn; -- > 533935876
-- tls227_pers_publn count: 533935876


DROP TABLE IF EXISTS tls228_docdb_fam_citn;
CREATE TABLE tls228_docdb_fam_citn (
    docdb_family_id integer DEFAULT 0 NOT NULL,
    cited_docdb_family_id integer DEFAULT 0 NOT NULL
);
copy tls228_docdb_fam_citn(docdb_family_id,cited_docdb_family_id) from '/tmp/tls228_docdb_fam_citn_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls228_docdb_fam_citn ADD PRIMARY KEY (docdb_family_id, cited_docdb_family_id);
select count(*) from tls228_docdb_fam_citn; -- > 307465107
-- tls228_docdb_fam_citn count: 307465107


DROP TABLE IF EXISTS tls229_appln_nace2;
CREATE TABLE tls229_appln_nace2 (
    appln_id integer DEFAULT 0 NOT NULL,
    nace2_code varchar(5) DEFAULT '' NOT NULL,
    weight numeric DEFAULT 1 NOT NULL
);
copy tls229_appln_nace2(appln_id,nace2_code,weight) from '/tmp/tls229_appln_nace2_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls229_appln_nace2 ADD PRIMARY KEY (appln_id, nace2_code);
select count(*) from tls229_appln_nace2; -- > 166322438
-- tls229_appln_nace2 count: 166322438


DROP TABLE IF EXISTS tls230_appln_techn_field;
CREATE TABLE tls230_appln_techn_field (
    appln_id integer DEFAULT 0 NOT NULL,
    techn_field_nr smallint DEFAULT 0 NOT NULL,
    weight numeric DEFAULT 1 NOT NULL
);
copy tls230_appln_techn_field(appln_id,techn_field_nr,weight) from '/tmp/tls230_appln_techn_field_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls230_appln_techn_field ADD PRIMARY KEY (appln_id, techn_field_nr);
select count(*) from tls230_appln_techn_field; -- > 166549096
-- tls230_appln_techn_field count: 166549096


DROP TABLE IF EXISTS tls231_inpadoc_legal_event;
CREATE TABLE tls231_inpadoc_legal_event (
    event_id integer DEFAULT 0 NOT NULL,
    appln_id integer DEFAULT 0 NOT NULL,
    event_seq_nr smallint DEFAULT 0,
    event_type char(3) DEFAULT '',
    event_auth char(2) DEFAULT '',
    event_code varchar(4)  DEFAULT '',
    event_filing_date date DEFAULT '9999-12-31' NOT NULL,
    event_publn_date date DEFAULT '9999-12-31' NOT NULL,
    event_effective_date date DEFAULT '9999-12-31' NOT NULL,
    event_text text DEFAULT '',
    ref_doc_auth char(2) DEFAULT '',
    ref_doc_nr varchar(20) DEFAULT '',
    ref_doc_kind char(2) DEFAULT '',
    ref_doc_date date DEFAULT '9999-12-31' NOT NULL,
    ref_doc_text text DEFAULT '',
    party_type varchar(3) DEFAULT '',
    party_seq_nr smallint default '0',
    party_new text DEFAULT '',
    party_old text DEFAULT '',
    spc_nr varchar(40) DEFAULT '',
    spc_filing_date date DEFAULT '9999-12-31' NOT NULL,
    spc_patent_expiry_date date DEFAULT '9999-12-31' NOT NULL,
    spc_extension_date date DEFAULT '9999-12-31' NOT NULL,
    spc_text text DEFAULT '',
    designated_states text DEFAULT '',
    extension_states varchar(30) DEFAULT '',
    fee_country char(2) DEFAULT '',
    fee_payment_date date DEFAULT '9999-12-31' NOT NULL,
    fee_renewal_year smallint DEFAULT '9999' NOT NULL,
    fee_text text DEFAULT '',
    lapse_country char(2) DEFAULT '',
    lapse_date date  DEFAULT '9999-12-31' NOT NULL,
    lapse_text text DEFAULT '',
    reinstate_country char(2) DEFAULT '',
    reinstate_date date DEFAULT '9999-12-31' NOT NULL,
    reinstate_text text DEFAULT '',
    class_scheme varchar(4) DEFAULT '',
    class_symbol varchar(50) DEFAULT ''
);
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part01.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part02.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part03.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part04.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part05.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part06.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part07.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part08.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part09.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part10.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part11.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part12.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part13.csv' CSV header ENCODING 'UTF8';
copy tls231_inpadoc_legal_event(event_id,appln_id,event_seq_nr,event_type,event_auth,event_code,event_filing_date,event_publn_date,event_effective_date,event_text,ref_doc_auth,ref_doc_nr,ref_doc_kind,ref_doc_date,ref_doc_text,party_type,party_seq_nr,party_new,party_old,spc_nr,spc_filing_date,spc_patent_expiry_date,spc_extension_date,spc_text,designated_states,extension_states,fee_country,fee_payment_date,fee_renewal_year,fee_text,lapse_country,lapse_date,lapse_text,reinstate_country,reinstate_date,reinstate_text,class_scheme,class_symbol) from '/tmp/tls231_inpadoc_legal_event_part14.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls231_inpadoc_legal_event ADD PRIMARY KEY (event_id);
select count(*) from tls231_inpadoc_legal_event; -- > 498252938
-- tls231_inpadoc_legal_event count: 498252938


DROP TABLE IF EXISTS tls801_country;
CREATE TABLE tls801_country (
    ctry_code char(2) DEFAULT '' NOT NULL,
    iso_alpha3 varchar(3) DEFAULT '' NOT NULL,
    st3_name varchar(100) DEFAULT '' NOT NULL,
    organisation_flag char(1) DEFAULT '' NOT NULL,
    continent varchar(25) DEFAULT '' NOT NULL,
    eu_member varchar(1) DEFAULT '' NOT NULL,
    epo_member varchar(1) DEFAULT '' NOT NULL,
    oecd_member varchar(1) DEFAULT '' NOT NULL,
    discontinued varchar(1) DEFAULT '' NOT NULL
);
copy tls801_country(ctry_code,iso_alpha3,st3_name,organisation_flag,continent,eu_member,epo_member,oecd_member,discontinued) from '/tmp/tls801_country_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls801_country ADD PRIMARY KEY (ctry_code);
select count(*) from tls801_country; -- > 242
--tls801_country count: 242


DROP TABLE IF EXISTS tls803_legal_event_code;
CREATE TABLE tls803_legal_event_code (
    event_auth char(2) DEFAULT '' NOT NULL,
    event_code varchar(4) DEFAULT '' NOT NULL,
    event_descr varchar(250) DEFAULT '',
    event_descr_orig varchar(250) DEFAULT '',
    event_category_code char(1) DEFAULT '',
    event_category_title varchar(100) DEFAULT ''
);
copy tls803_legal_event_code(event_auth,event_code,event_descr,event_descr_orig,event_category_code,event_category_title) from '/tmp/tls803_legal_event_code_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls803_legal_event_code ADD PRIMARY KEY (event_auth, event_code);
select count(*) from tls803_legal_event_code -- > 4185
-- tls803_legal_event_code count: 4185


DROP TABLE IF EXISTS tls901_techn_field_ipc;
CREATE TABLE tls901_techn_field_ipc (
    ipc_maingroup_symbol varchar(8) DEFAULT '' NOT NULL,
    techn_field_nr smallint DEFAULT 0 NOT NULL,
    techn_sector varchar(50) DEFAULT '' NOT NULL,
    techn_field varchar(50) DEFAULT '' NOT NULL
);
copy tls901_techn_field_ipc(ipc_maingroup_symbol,techn_field_nr,techn_sector,techn_field) from '/tmp/tls901_techn_field_ipc_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls901_techn_field_ipc ADD PRIMARY KEY (ipc_maingroup_symbol);
select count(*) from tls901_techn_field_ipc; -- > 771
-- tls901_techn_field_ipc count: 771


DROP TABLE IF EXISTS tls902_ipc_nace2;
CREATE TABLE tls902_ipc_nace2 (
    ipc varchar(8) DEFAULT '' NOT NULL,
    not_with_ipc varchar(8) DEFAULT '' NOT NULL,
    unless_with_ipc varchar(8) DEFAULT '' NOT NULL,
    nace2_code varchar(5) DEFAULT '' NOT NULL,
    nace2_weight smallint DEFAULT 1 NOT NULL,
    nace2_descr varchar(150) DEFAULT '' NOT NULL
);
copy tls902_ipc_nace2(ipc,not_with_ipc,unless_with_ipc,nace2_code,nace2_weight,nace2_descr) from '/tmp/tls902_ipc_nace2_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls902_ipc_nace2 ADD PRIMARY KEY (ipc, not_with_ipc, unless_with_ipc, nace2_code);
select count(*) from tls902_ipc_nace2; -- > 863
-- tls902_ipc_nace2 count: 863


DROP TABLE IF EXISTS tls904_nuts;
CREATE TABLE tls904_nuts (
    nuts varchar(5) DEFAULT ('') NOT NULL,
    nuts_level smallint DEFAULT '0',
    nuts_label varchar(250) DEFAULT ''
);
copy tls904_nuts(nuts,nuts_level,nuts_label) from '/tmp/tls904_nuts_part01.csv' CSV header ENCODING 'UTF8';
ALTER TABLE tls904_nuts ADD PRIMARY KEY (nuts);
CREATE INDEX idx_nuts_level ON tls904_nuts (nuts, nuts_level);
select count(*) from tls904_nuts; -- > 2056
-- tls904_nuts count: 2056
