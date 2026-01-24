# BigQuery Setup on Mac

## 1. Install Google Cloud SDK

```bash
# Install via Homebrew
brew install --cask google-cloud-sdk

# Or download directly from:
# https://cloud.google.com/sdk/docs/install
```

## 2. Initialize and Login

```bash
# Initialize gcloud
gcloud init

# Login to your Google account
gcloud auth login

# Set your project
gcloud config set project patstat-mtc

# Setup application credentials (for Python)
gcloud auth application-default login
```

## 3. Install Python Dependencies

```bash
pip3 install google-cloud-bigquery pyarrow pandas
```

## 4. Verify Setup

```bash
# Test CLI
bq ls

# Should show your datasets (or empty if new project)
```

## 5. Run Migration

```bash
cd migration/

# List available CSV files
python3 migrate_to_bq.py /path/to/patstat/csvs --list

# Dry run (no actual upload)
python3 migrate_to_bq.py /path/to/patstat/csvs --dry-run

# Execute migration
python3 migrate_to_bq.py /path/to/patstat/csvs
```

## Troubleshooting

**"Application Default Credentials not found"**
```bash
gcloud auth application-default login
```

**"Permission denied"**
```bash
# Ensure you're using the right project
gcloud config set project patstat-mtc
```

**"Dataset not found"**
```bash
# Create the dataset first
bq mk --dataset patstat-mtc:patstat
```
