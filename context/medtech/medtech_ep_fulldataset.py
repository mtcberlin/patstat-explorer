#!/usr/bin/env python3
"""
BVMed Medical Patent Export Script
=================================

Exports comprehensive medical patent data from PATSTAT database for BVMed analysis.

Features:
- EP patent applications (2012-2022)
- Medical technology focus (12 CPC classes)
- Applicant information with countries
- IPC Level A classifications with descriptions
- Semicolon-separated CSV output

Output CSV Columns:
- application_number: EP application number
- appln_filing_date: Filing date (YYYY-MM-DD)
- filing_year: Filing year as integer
- applicants: All applicants (comma-separated)
- applicant_countries: Applicant countries (comma-separated)
- ipc_main_classes: IPC main classes like A61B, A61C (comma-separated)
- ipc_descriptions: Human-readable descriptions (comma-separated)
- ipc_classes: Full IPC level A classifications (comma-separated)

Author: Medical Technology Analysis System
Based on: BVMed CPC Search Query 5c - alle EP Anmeldungen.sql
"""

import pandas as pd
import os
from datetime import datetime
from pathlib import Path

from epo.tipdata.patstat import PatstatClient
from epo.tipdata.patstat.database.models import (
    TLS201_APPLN, TLS206_PERSON, TLS207_PERS_APPLN,
    TLS209_APPLN_IPC, TLS224_APPLN_CPC
)
from sqlalchemy import func, and_, or_


class BVMedExporter:
    """
    Medical patent data exporter for BVMed analysis.

    Exports EP patent applications in medical technology areas
    with comprehensive applicant and classification information.
    """

    def __init__(self):
        """Initialize database connection and configuration."""
        self.patstat = PatstatClient(env='PROD')
        self.db = self.patstat.orm()

        # Medical technology CPC classes from BVMed query
        self.medical_cpc_classes = [
            'H05G%', 'G16H%', 'A61B%', 'A61C%', 'A61F%', 'A61G%',
            'A61H%', 'A61J%', 'A61K%', 'A61L%', 'A61M%', 'A61N%'
        ]

        # IPC class descriptions for medical technologies
        self.ipc_descriptions = {
            'H05G': 'X-ray Technique',
            'G16H': 'Healthcare Informatics',
            'A61B': 'Diagnosis, Surgery, Identification',
            'A61C': 'Dentistry, Oral Hygiene',
            'A61F': 'Filters, Protheses, Orthotics',
            'A61G': 'Transport, Personal Conveyances',
            'A61H': 'Physical Therapy Apparatus',
            'A61J': 'Containers for Medicines',
            'A61K': 'Medicinal Preparations (Drug Delivery)',
            'A61L': 'Sterilisation, Disinfection',
            'A61M': 'Devices for Introducing Media',
            'A61N': 'Electrotherapy, Magnetotherapy'
        }

    def build_query(self, start_year=2012, end_year=2022, jurisdiction='EP'):
        """
        Build the main export query.

        Args:
            start_year (int): Start year for applications
            end_year (int): End year for applications
            jurisdiction (str): Patent jurisdiction

        Returns:
            SQLAlchemy Query: Configured query object
        """
        # Build CPC filter conditions
        cpc_conditions = [
            TLS224_APPLN_CPC.cpc_class_symbol.like(pattern)
            for pattern in self.medical_cpc_classes
        ]

        # Main query
        query = self.db.query(
            func.concat(
                TLS201_APPLN.appln_auth,
                TLS201_APPLN.appln_nr,
                TLS201_APPLN.appln_kind
            ).label('application_number'),
            TLS201_APPLN.appln_filing_date.label('appln_filing_date'),
            func.extract('year', TLS201_APPLN.appln_filing_date).label('filing_year'),
            func.string_agg(
                func.distinct(TLS206_PERSON.person_name),
                ' | '
            ).label('applicants'),
            func.string_agg(
                func.distinct(TLS206_PERSON.person_ctry_code),
                ' | '
            ).label('applicant_countries'),
            func.string_agg(
                func.distinct(func.left(TLS209_APPLN_IPC.ipc_class_symbol, 4)),
                ', '
            ).label('ipc_main_classes'),
            func.string_agg(
                func.distinct(TLS209_APPLN_IPC.ipc_class_symbol),
                ', '
            ).label('ipc_classes')
        ).join(
            TLS224_APPLN_CPC, TLS201_APPLN.appln_id == TLS224_APPLN_CPC.appln_id
        ).join(
            TLS207_PERS_APPLN, TLS201_APPLN.appln_id == TLS207_PERS_APPLN.appln_id
        ).join(
            TLS206_PERSON, TLS207_PERS_APPLN.person_id == TLS206_PERSON.person_id
        ).outerjoin(
            TLS209_APPLN_IPC, TLS201_APPLN.appln_id == TLS209_APPLN_IPC.appln_id
        ).filter(
            and_(
                TLS201_APPLN.appln_filing_year.between(start_year, end_year),
                TLS201_APPLN.appln_auth == jurisdiction,
                or_(*cpc_conditions),
                TLS207_PERS_APPLN.applt_seq_nr > 0,
                TLS206_PERSON.person_name.isnot(None),
                or_(
                    TLS209_APPLN_IPC.ipc_class_level == 'A',
                    TLS209_APPLN_IPC.ipc_class_level.is_(None)
                )
            )
        ).group_by(
            TLS201_APPLN.appln_auth,
            TLS201_APPLN.appln_nr,
            TLS201_APPLN.appln_kind,
            TLS201_APPLN.appln_filing_date,
            func.extract('year', TLS201_APPLN.appln_filing_date)
        ).order_by(
            TLS201_APPLN.appln_filing_date
        )

        return query

    def add_ipc_descriptions(self, df):
        """
        Add IPC descriptions based on main classes.

        Args:
            df (pandas.DataFrame): DataFrame with ipc_main_classes column

        Returns:
            pandas.DataFrame: DataFrame with added ipc_descriptions column
        """
        def map_descriptions(main_classes_str):
            if pd.isna(main_classes_str) or main_classes_str == '':
                return ''

            main_classes = [cls.strip() for cls in str(main_classes_str).split(',')]
            descriptions = []

            for main_class in main_classes:
                if main_class in self.ipc_descriptions:
                    descriptions.append(self.ipc_descriptions[main_class])
                else:
                    descriptions.append(f'Unknown ({main_class})')

            return ', '.join(descriptions)

        df['ipc_descriptions'] = df['ipc_main_classes'].apply(map_descriptions)
        return df

    def export_csv(self, output_path=None, start_year=2012, end_year=2022, jurisdiction='EP'):
        """
        Execute query and export results to CSV.

        Args:
            output_path (str, optional): Output file path
            start_year (int): Start year for export
            end_year (int): End year for export
            jurisdiction (str): Patent jurisdiction

        Returns:
            str: Path to created CSV file
        """
        print(f"🚀 Starting BVMed medical patent export")
        print(f"📅 Period: {start_year}-{end_year}")
        print(f"🏛️ Jurisdiction: {jurisdiction}")

        # Generate output path
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            charts_dir = Path("charts_data")
            charts_dir.mkdir(exist_ok=True)
            output_path = charts_dir / f"medtech_ep_fulldataset_{jurisdiction}_{start_year}_{end_year}_{timestamp}.csv"

        # Execute query
        print("📊 Executing database query...")
        query = self.build_query(start_year, end_year, jurisdiction)
        df = pd.read_sql(query.statement, self.db.bind)

        # Add IPC descriptions
        df = self.add_ipc_descriptions(df)

        # Reorder columns
        df = df[[
            'application_number', 'appln_filing_date', 'filing_year',
            'applicants', 'applicant_countries',
            'ipc_main_classes', 'ipc_descriptions', 'ipc_classes'
        ]]

        # Export CSV
        print(f"💾 Writing CSV: {output_path}")
        df.to_csv(output_path, index=False, encoding='utf-8', sep=';', quoting=0)

        # Print statistics
        file_size_mb = os.path.getsize(output_path) / 1024 / 1024
        unique_applicants = df['applicants'].str.split(', ').explode().nunique()
        unique_countries = df['applicant_countries'].str.split(', ').explode().nunique()
        unique_main_classes = df['ipc_main_classes'].str.split(', ').explode().nunique()
        unique_ipc_classes = df['ipc_classes'].str.split(', ').explode().nunique()

        print(f"✅ Export completed successfully!")
        print(f"📊 Records exported: {len(df):,}")
        print(f"📁 File size: {file_size_mb:.2f} MB")
        print(f"📅 Date range: {df['appln_filing_date'].min()} to {df['appln_filing_date'].max()}")
        print(f"📅 Filing years: {df['filing_year'].min():.0f}-{df['filing_year'].max():.0f}")
        print(f"🏢 Unique applicants: {unique_applicants:,}")
        print(f"🌍 Countries: {unique_countries}")
        print(f"🔬 IPC main classes: {unique_main_classes}")
        print(f"🔬 IPC level A classes: {unique_ipc_classes}")

        return str(output_path)

    def preview(self, limit=5, start_year=2012, end_year=2023, jurisdiction='EP'):
        """
        Show a preview of the data.

        Args:
            limit (int): Number of records to show
            start_year (int): Start year
            end_year (int): End year
            jurisdiction (str): Patent jurisdiction

        Returns:
            pandas.DataFrame: Preview data
        """
        print(f"👀 Generating preview ({limit} records)")
        query = self.build_query(start_year, end_year, jurisdiction).limit(limit)
        df = pd.read_sql(query.statement, self.db.bind)
        df = self.add_ipc_descriptions(df)

        return df[[
            'application_number', 'appln_filing_date', 'filing_year',
            'applicants', 'applicant_countries',
            'ipc_main_classes', 'ipc_descriptions', 'ipc_classes'
        ]]

    def close(self):
        """Close database connection."""
        if hasattr(self, 'db'):
            self.db.close()


def main():
    """Main execution function."""
    print("=" * 60)
    print("🏥 BVMed Medical Patent Export")
    print("📊 EP Applications 2012-2022")
    print("=" * 60)

    exporter = BVMedExporter()

    try:
        # Show preview
        print("\n👀 Data Preview:")
        preview = exporter.preview()
        print(preview.to_string(max_colwidth=50))

        # Full export
        print(f"\n🚀 Starting full export...")
        output_file = exporter.export_csv()
        print(f"\n📁 Output: {output_file}")

    except Exception as e:
        print(f"❌ Export failed: {str(e)}")
        raise
    finally:
        exporter.close()


if __name__ == "__main__":
    main()