# Abra-Q Integration Documentation

## Overview

The PATSTAT Explorer now supports multiple query generation providers through a configurable architecture. This allows seamless switching between Anthropic's Claude API and TTC's Abra-Q service for SQL query generation.

## Architecture

```
┌─────────────────────────────────────────┐
│  UI Layer (modules/ui.py)              │
│  render_ai_builder_page()              │
└──────────────┬──────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────┐
│  Logic Layer (modules/logic.py)         │
│  generate_sql_query(request)            │
│    ├─ Check QUERY_PROVIDER env var     │
│    ├─ Route to: claude OR abra-q       │
│    └─ Normalize response format        │
└──────┬──────────────────┬───────────────┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌─────────────────────┐
│ Claude API   │   │ Abra-Q Client       │
│ (default)    │   │ (NEW)               │
└──────────────┘   │ - Authentication    │
                   │ - Token management  │
                   │ - Query API calls   │
                   └─────────────────────┘
```

## Components

### 1. Abra-Q Client (`modules/abra_q_client.py`)

**Purpose**: Handles all communication with the Abra-Q API service

**Key Features**:
- Automatic authentication with token caching
- Token expiry management (24-hour lifetime with 5-minute buffer)
- Normalized response format matching Claude API
- Error handling and timeout management

**Main Classes/Functions**:
- `AbraQClient`: Main client class
  - `generate_query(question)`: Generate SQL from natural language
  - `get_sample_queries()`: Fetch existing sample queries
  - `generate_new_sample_queries()`: Request new sample generation
- `get_abraq_client()`: Factory function to get configured client
- `is_abraq_available()`: Check if Abra-Q is properly configured

### 2. Modified Logic Layer (`modules/logic.py`)

**Changes**:
- Added provider routing in `generate_sql_query()`
- Modified `is_ai_available()` to check configured provider
- Maintains backward compatibility with Claude API

### 3. Configuration (`.env`)

New environment variables:
```bash
# Query Provider Configuration
QUERY_PROVIDER=abra-q  # Options: "claude" or "abra-q"

# Abra-Q Configuration
ABRAQ_API_URL=https://5i3vp2k9zz.eu-central-1.awsapprunner.com
ABRAQ_EMAIL=patstat@mtc.berlin
ABRAQ_PASSWORD=ZjC_zRf4nDpUIgWd2CbyA
ABRAQ_DATASOURCE=arne-patstat
```

## Configuration

### Switching Providers

**To use Abra-Q** (TTC's service):
```bash
QUERY_PROVIDER=abra-q
```

**To use Claude API** (Anthropic):
```bash
QUERY_PROVIDER=claude
```

Or simply remove the `QUERY_PROVIDER` variable (Claude is default).

### Abra-Q Setup

1. Ensure these environment variables are set in `.env`:
   ```bash
   ABRAQ_API_URL=<backend-url>
   ABRAQ_EMAIL=<your-email>
   ABRAQ_PASSWORD=<your-password>
   ABRAQ_DATASOURCE=<datasource-name>
   ```

2. Set the provider:
   ```bash
   QUERY_PROVIDER=abra-q
   ```

3. Restart the Streamlit application

### Claude API Setup

1. Ensure `ANTHROPIC_API_KEY` is set in `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   ```

2. Set the provider (or leave unset for default):
   ```bash
   QUERY_PROVIDER=claude
   ```

3. Restart the Streamlit application

## API Credentials

### Abra-Q Service Endpoints

- **Frontend URL**: https://yabj2bhds3.eu-central-1.awsapprunner.com
- **Backend URL**: https://5i3vp2k9zz.eu-central-1.awsapprunner.com

### Available Credentials

**Admin Account** (full access):
- Email: `arne.krueger@mtc.berlin`
- Password: `ojwPJf2Q^O7Kf%`

**Read-Only Account** (query and read access):
- Email: `patstat@mtc.berlin`
- Password: `ZjC_zRf4nDpUIgWd2CbyA`

> ⚠️ **Security Note**: The read-only account is currently configured in `.env` for safety. Use admin credentials only when needed for datasource management.

## Testing

### Running Integration Tests

A comprehensive test suite validates all integration components:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
python test_abraq_integration.py
```

### Test Coverage

The test suite validates:
1. ✅ **Availability Check**: Verifies Abra-Q configuration
2. ✅ **Authentication**: Tests login and token retrieval
3. ✅ **Query Generation**: Validates SQL generation from natural language
4. ✅ **Provider Routing**: Confirms routing logic works correctly

### Expected Output

```
╔==========================================================╗
║               ABRA-Q INTEGRATION TESTS                   ║
╚==========================================================╝

============================================================
TEST 1: Abra-Q Availability Check
============================================================
✓ Abra-Q Available: True
✓ API URL: https://5i3vp2k9zz.eu-central-1.awsapprunner.com
✓ Datasource: arne-patstat
✓ Email: patstat@mtc.berlin
✓ Password: [CONFIGURED]

============================================================
TEST 2: Abra-Q Authentication
============================================================
✓ Authentication successful
✓ Token received: eyJhbGc...

============================================================
TEST 3: Query Generation
============================================================
✓ Query generation successful
✓ Explanation and SQL received

============================================================
TEST 4: Provider Routing
============================================================
✓ Provider routing successful
✓ Received SQL through routing layer

============================================================
TEST SUMMARY
============================================================
Results: 4/4 tests passed
============================================================
```

## Usage

### End-User Experience

The integration is **completely transparent** to end users:

1. Navigate to **🤖 AI Query Builder** page
2. Enter natural language query description
3. Click **Generate Query**
4. System automatically uses the configured provider (Abra-Q or Claude)
5. Results displayed identically regardless of provider

### Developer Experience

**No code changes needed** when switching providers. Simply update `.env`:

```bash
# Switch to Abra-Q
QUERY_PROVIDER=abra-q

# Switch back to Claude
QUERY_PROVIDER=claude
```

Then restart the application.

## Response Format

Both providers return normalized responses:

```python
{
    'success': bool,
    'sql': str,           # Generated SQL query
    'explanation': str,   # Query explanation
    'notes': str,         # Additional notes (optional)
    'error': str | None   # Error message if success=False
}
```

## Error Handling

The integration includes comprehensive error handling:

- **Authentication Failures**: Clear error messages with credential check prompts
- **Timeout Handling**: 30-second timeout for query generation
- **Token Expiry**: Automatic re-authentication when token expires
- **API Errors**: Detailed error messages with context

## Troubleshooting

### "Abra-Q not configured" Error

**Cause**: Missing or incorrect environment variables

**Solution**:
1. Verify `.env` contains all required Abra-Q variables
2. Check credentials are correct
3. Restart the application to reload environment

### 401 Unauthorized Error

**Cause**: Invalid credentials or token issues

**Solution**:
1. Verify `ABRAQ_EMAIL` and `ABRAQ_PASSWORD` are correct
2. Check account has access to the datasource
3. Delete any cached tokens (restart application)

### Query Generation Timeout

**Cause**: Complex queries or slow service response

**Solution**:
1. Simplify the natural language request
2. Check Abra-Q service status
3. Increase timeout in `abra_q_client.py` if needed

## Performance Considerations

### Token Caching
- Tokens are cached for 24 hours
- Automatic re-authentication before expiry
- Reduces authentication overhead

### Timeouts
- Authentication: 10 seconds
- Query generation: 30 seconds
- Sample queries: 10 seconds

## Future Enhancements

Potential improvements for the integration:

1. **Multi-Provider Support**: Allow multiple providers simultaneously
2. **Provider Fallback**: Auto-switch if primary provider fails
3. **Query History**: Store generated queries by provider
4. **Performance Metrics**: Track response times per provider
5. **Sample Query Integration**: Use Abra-Q sample queries in UI

## Development Notes

### Adding New Providers

To add additional query generation providers:

1. Create client module in `modules/` (e.g., `new_provider_client.py`)
2. Implement these functions:
   - `get_newprovider_client()`
   - `is_newprovider_available()`
3. Add provider case in `generate_sql_query()` in `logic.py`
4. Add provider case in `is_ai_available()` in `logic.py`
5. Document new provider configuration

### Testing New Providers

1. Create test script following `test_abraq_integration.py` pattern
2. Test availability, authentication, and query generation
3. Validate response format normalization
4. Document provider-specific quirks

## References

### Related Files
- `modules/abra_q_client.py`: Abra-Q client implementation
- `modules/logic.py`: Provider routing logic
- `.env`: Configuration and credentials
- `test_abraq_integration.py`: Integration test suite

### External Documentation
- Abra-Q Frontend: https://yabj2bhds3.eu-central-1.awsapprunner.com
- Abra-Q Backend API: https://5i3vp2k9zz.eu-central-1.awsapprunner.com

## Changelog

### 2026-02-02 - Initial Integration
- ✅ Created `modules/abra_q_client.py`
- ✅ Modified `modules/logic.py` for provider routing
- ✅ Updated `.env` with Abra-Q configuration
- ✅ Created integration test suite
- ✅ All tests passing (4/4)
- ✅ Documentation complete

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review test output for specific errors
3. Verify configuration in `.env`
4. Contact TTC for Abra-Q service issues
5. Contact Anthropic for Claude API issues
