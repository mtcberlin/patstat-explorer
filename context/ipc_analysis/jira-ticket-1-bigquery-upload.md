# Ticket 1: Upload IPC Hierarchy to BigQuery

## Summary

Upload the IPC classification hierarchy (SQLite) as new reference table `tls_ipc_hierarchy` to BigQuery. This is the prerequisite for both the MCP extension and the training guide.

## Work Order

1. Run the provided upload script against `patent-classification-2025.db` (79,833 entries, IPC 2025.01)
2. Verify generated columns: `symbol_patstat` (PATSTAT space-padded format) and `title_full` (concatenated ancestor chain)
3. Validate JOIN to `tls209_appln_ipc.ipc_class_symbol` via `symbol_patstat`
4. Run 4 test queries from spec (Section "Testing Queries")

## Deliverable

`tls_ipc_hierarchy` table live in BigQuery, 79,833 rows, all columns populated. Conversion functions and upload script provided in spec.

## Spec

`mcp-patstat-extension-spec.md`, Section "Extending PATSTAT with the IPC Hierarchy Database"
