-- Compare your counts with EPO counts available in RowCount_EPO_result.txt

SELECT 'tls201_appln count:', count(*) FROM tls201_appln ; 
SELECT 'tls202_appln_title count:', count(*) FROM tls202_appln_title ; 
SELECT 'tls203_appln_abstr count:', count(*) FROM tls203_appln_abstr ; 
SELECT 'tls204_appln_prior count:', count(*) FROM tls204_appln_prior ; 
SELECT 'tls205_tech_rel count:', count(*) FROM tls205_tech_rel ; 
SELECT 'tls206_person count:', count(*) FROM tls206_person ; 
SELECT 'tls207_pers_appln count:', count(*) FROM tls207_pers_appln ; 
SELECT 'tls209_appln_ipc count:', count(*) FROM tls209_appln_ipc ; 
SELECT 'tls210_appln_n_cls count:', count(*) FROM tls210_appln_n_cls ;
SELECT 'tls211_pat_publn count:', count(*) FROM tls211_pat_publn ; 
SELECT 'tls212_citation count:', count(*) FROM tls212_citation ; 
SELECT 'tls214_npl_publn count:', count(*) FROM tls214_npl_publn ; 
SELECT 'tls215_citn_categ count:', count(*) FROM tls215_citn_categ ; 
SELECT 'tls216_appln_contn count:', count(*) FROM tls216_appln_contn ; 
SELECT 'tls222_appln_jp_class count:', count(*) FROM tls222_appln_jp_class ; 
SELECT 'tls224_appln_cpc count:', count(*) FROM tls224_appln_cpc ; 
SELECT 'tls225_docdb_fam_cpc count:', count(*) FROM tls225_docdb_fam_cpc ; 
SELECT 'tls226_person_orig count:', count(*) FROM tls226_person_orig ; 
SELECT 'tls227_pers_publn count:', count(*) FROM tls227_pers_publn ; 
SELECT 'tls228_docdb_fam_citn count:', count(*) FROM tls228_docdb_fam_citn ; 
SELECT 'tls229_appln_nace2 count:', count(*) FROM tls229_appln_nace2 ; 
SELECT 'tls230_appln_techn_field count:', count(*) FROM tls230_appln_techn_field ; 
SELECT 'tls231_inpadoc_legal_event count:', count(*) FROM tls231_inpadoc_legal_event ; 
SELECT 'tls801_country count:', count(*) FROM tls801_country ; 
SELECT 'tls803_legal_event_code count:', count(*) FROM tls803_legal_event_code ;
SELECT 'tls901_techn_field_ipc count:', count(*) FROM tls901_techn_field_ipc ; 
SELECT 'tls902_ipc_nace2 count:', count(*) FROM tls902_ipc_nace2 ;
SELECT 'tls904_nuts count:', count(*) FROM tls904_nuts ;

