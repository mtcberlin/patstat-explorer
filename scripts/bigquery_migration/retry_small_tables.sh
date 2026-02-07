#!/bin/bash
# Retry failed tables (EXCLUDING tls203 and tls231 - the monsters)
# tls203_appln_abstr: 88 GB - SKIP for now
# tls231_inpadoc_legal_event: 121 GB - SKIP for now

LOGFILE="migration_retry_$(date +%Y%m%d_%H%M%S).log"

echo "Starting migration retry at $(date)" | tee -a "$LOGFILE"
echo "Skipping large tables: tls203_appln_abstr (88GB), tls231_inpadoc_legal_event (121GB)" | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"

SMALL_TABLES=(
  "tls201_appln"
  "tls206_person"
  "tls209_appln_ipc"
  "tls211_pat_publn"
  "tls212_citation"
  "tls214_npl_publn"
  "tls215_citn_categ"
  "tls222_appln_jp_class"
  "tls224_appln_cpc"
  "tls225_docdb_fam_cpc"
  "tls226_person_orig"
  "tls227_pers_publn"
)

SUCCESS=0
FAILED=0

for table in "${SMALL_TABLES[@]}"; do
  echo "==========================================" | tee -a "$LOGFILE"
  echo "[$(date +%H:%M:%S)] Starting: $table" | tee -a "$LOGFILE"
  echo "==========================================" | tee -a "$LOGFILE"

  python3 migrate_to_bq.py ~/mnt/synology --table "$table" 2>&1 | tee -a "$LOGFILE"

  if [ ${PIPESTATUS[0]} -eq 0 ]; then
    SUCCESS=$((SUCCESS + 1))
    echo "[$(date +%H:%M:%S)] ✓ $table completed successfully" | tee -a "$LOGFILE"
  else
    FAILED=$((FAILED + 1))
    echo "[$(date +%H:%M:%S)] ✗ $table FAILED" | tee -a "$LOGFILE"
  fi
  echo "" | tee -a "$LOGFILE"
done

echo "==========================================" | tee -a "$LOGFILE"
echo "Migration complete at $(date)" | tee -a "$LOGFILE"
echo "Success: $SUCCESS, Failed: $FAILED" | tee -a "$LOGFILE"
echo "==========================================" | tee -a "$LOGFILE"
echo "" | tee -a "$LOGFILE"
echo "Next step: Load large tables with:" | tee -a "$LOGFILE"
echo "  python3 migrate_to_bq.py ~/mnt/synology --table tls203_appln_abstr" | tee -a "$LOGFILE"
echo "  python3 migrate_to_bq.py ~/mnt/synology --table tls231_inpadoc_legal_event" | tee -a "$LOGFILE"
