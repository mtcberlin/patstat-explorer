"""
Medical Patent Analysis for PATSTAT BigQuery
===========================================

Analyze EP patent family activities in 12 medical technology IPC classes (2012-2022).
Transforms PostgreSQL queries to PATSTAT BigQuery format for chart creation.

Author: Claude Code with Arne Krueger, mtc, 2025
Based on: PostgreSQL queries for BVMed analysis
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# PATSTAT imports
from epo.tipdata.patstat import PatstatClient
from epo.tipdata.patstat.database.models import (
    TLS201_APPLN, TLS206_PERSON, TLS207_PERS_APPLN, TLS209_APPLN_IPC, TLS901_TECHN_FIELD_IPC
)
from sqlalchemy import func, text, case, and_, or_


class MedicalPatentAnalyzer:
    """Analyzer for medical technology patents in PATSTAT"""

    # Medical technology IPC classes for analysis (with descriptive names)
    MEDICAL_IPC_CLASSES = {
        'H05G': 'X-ray Technique',
        'G16H': 'Healthcare Informatics',
        'A61B': 'Diagnosis, Surgery, Identification',
        'A61C': 'Dentistry, Oral Hygiene',
        'A61F': 'Filters, Protheses, Orthotics',
        'A61G': 'Transport, Personal Conveyances',
        'A61H': 'Physical Therapy Apparatus',
        'A61J': 'Containers for Medicines',
        'A61K': 'Medicinal Preparations',
        'A61L': 'Sterilisation, Disinfection',
        'A61M': 'Devices for Introducing Media',
        'A61N': 'Electrotherapy, Magnetotherapy'
    }

    def __init__(self):
        """Initialize PATSTAT connection"""
        self.patstat = None
        self.db = None
        self.supported_jurisdictions = {
            'EP': 'European Patent Office',
            'DE': 'Germany (DPMA)',
            'US': 'United States (USPTO)',
            'CN': 'China (CNIPA)',
            'ALL': 'All PATSTAT jurisdictions'
        }
        self._connect()

    def _connect(self):
        """Establish PATSTAT connection"""
        try:
            self.patstat = PatstatClient(env='PROD')
            self.db = self.patstat.orm()
            print("🔗 PATSTAT connection established successfully")
        except Exception as e:
            print(f"❌ Connection error: {e}")
            raise

    def _get_ipc_class_filter(self):
        """Create IPC class filter conditions for medical technology classes"""
        conditions = []

        # Standard A61 classes (except A61K which needs special handling)
        standard_classes = ['H05G', 'G16H', 'A61B', 'A61C', 'A61F', 'A61G',
                           'A61H', 'A61J', 'A61K', 'A61L', 'A61M', 'A61N']

        for ipc_class in standard_classes:
            conditions.append(and_(
                TLS209_APPLN_IPC.ipc_class_symbol.like(f'{ipc_class}%'),
                TLS209_APPLN_IPC.ipc_class_level == 'A'
            ))

        # Special case for A61K40 (drug delivery systems)
        # conditions.append(and_(
        #    TLS209_APPLN_IPC.ipc_class_symbol.like('A61K%40%'),
        #    TLS209_APPLN_IPC.ipc_class_level == 'A'
        #))

        return or_(*conditions)

    def _get_jurisdiction_filter(self, jurisdictions):
        """Create jurisdiction filter conditions"""
        if isinstance(jurisdictions, str):
            jurisdictions = [jurisdictions]

        if 'ALL' in jurisdictions:
            return None  # No filter for all jurisdictions

        # Filter for specific jurisdictions
        conditions = []
        for jurisdiction in jurisdictions:
            if jurisdiction in self.supported_jurisdictions:
                conditions.append(TLS201_APPLN.appln_auth == jurisdiction)

        return or_(*conditions) if conditions else None

    def _get_ipc_class_case_statement(self):
        """Create CASE statement for IPC class categorization"""
        return case(
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('H05G%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'H05G'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('G16H%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'G16H'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61B%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61B'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61C%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61C'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61F%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61F'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61G%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61G'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61H%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61H'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61J%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61J'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61K%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61K'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61L%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61L'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61M%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61M'),
            (and_(TLS209_APPLN_IPC.ipc_class_symbol.like('A61N%'), TLS209_APPLN_IPC.ipc_class_level == 'A'), 'A61N'),
            else_=None
        ).label('ipc_class')

    def query_applications_by_year_and_class(self, start_year: int = 2012, end_year: int = 2022,
                                            jurisdictions=['EP']) -> pd.DataFrame:
        """
        Query 2: Aggregation by year and IPC class
        Shows application counts per year and class (12 medical classes)

        Args:
            start_year: Start year for analysis (default: 2012)
            end_year: End year for analysis (default: 2022)
            jurisdictions: List of jurisdictions to analyze (default: ['EP'])
                          Options: 'EP', 'DE', 'US', 'CN', 'ALL'

        Returns:
            DataFrame with columns: appln_filing_year, ipc_class, application_count, jurisdiction
        """
        jurisdiction_str = ', '.join(jurisdictions) if isinstance(jurisdictions, list) else jurisdictions
        print(f"🔍 Analyzing {jurisdiction_str} applications by year and IPC class ({start_year}-{end_year})...")

        try:
            # Get jurisdiction filter
            jurisdiction_filter = self._get_jurisdiction_filter(jurisdictions)

            # Build filter conditions
            filter_conditions = [
                TLS201_APPLN.appln_filing_year.between(start_year, end_year),
                self._get_ipc_class_filter()
            ]

            # Add jurisdiction filter if specified
            if jurisdiction_filter is not None:
                filter_conditions.append(jurisdiction_filter)

            # Create subquery for medical applications with IPC classification
            medical_apps_subquery = self.db.query(
                TLS201_APPLN.appln_id.label('appln_id'),
                TLS201_APPLN.appln_filing_year.label('appln_filing_year'),
                TLS201_APPLN.appln_auth.label('jurisdiction'),
                self._get_ipc_class_case_statement()
            ).join(
                TLS209_APPLN_IPC, TLS201_APPLN.appln_id == TLS209_APPLN_IPC.appln_id
            ).filter(
                and_(*filter_conditions)
            ).distinct().subquery()

            # Main aggregation query - include jurisdiction for comparative analysis
            results = self.db.query(
                medical_apps_subquery.c.appln_filing_year,
                medical_apps_subquery.c.jurisdiction,
                medical_apps_subquery.c.ipc_class,
                func.count(func.distinct(medical_apps_subquery.c.appln_id)).label('application_count')
            ).filter(
                medical_apps_subquery.c.ipc_class.isnot(None)
            ).group_by(
                medical_apps_subquery.c.appln_filing_year,
                medical_apps_subquery.c.jurisdiction,
                medical_apps_subquery.c.ipc_class
            ).order_by(
                medical_apps_subquery.c.appln_filing_year,
                medical_apps_subquery.c.jurisdiction,
                medical_apps_subquery.c.ipc_class
            ).all()

            # Convert to DataFrame
            df = pd.DataFrame(results, columns=['appln_filing_year', 'jurisdiction', 'ipc_class', 'application_count'])

            # Add class descriptions and jurisdiction descriptions for better charts
            df['ipc_class_description'] = df['ipc_class'].map(self.MEDICAL_IPC_CLASSES)
            df['jurisdiction_description'] = df['jurisdiction'].map(self.supported_jurisdictions)

            print(f"✅ Found {len(df)} year/class combinations with {df['application_count'].sum()} total applications")
            return df

        except Exception as e:
            print(f"❌ Error in applications by year/class query: {e}")
            raise

    def query_top_applicants_by_class(self, top_n: int = 10, start_year: int = 2012, end_year: int = 2022) -> pd.DataFrame:
        """
        Query 3: Top N applicants per IPC class
        Identifies market leaders in each technical category

        Args:
            top_n: Number of top applicants per class (default: 10)
            start_year: Start year for analysis (default: 2012)
            end_year: End year for analysis (default: 2022)

        Returns:
            DataFrame with columns: ipc_class, applicant_name, app_count, rank
        """
        print(f"🔍 Finding top {top_n} applicants per IPC class ({start_year}-{end_year})...")

        # Use reliable method with pandas ranking instead of complex SQL window functions
        return self._query_top_applicants_by_class_pandas_ranking(top_n, start_year, end_year)

    def _query_top_applicants_by_class_pandas_ranking(self, top_n: int, start_year: int, end_year: int) -> pd.DataFrame:
        """Reliable method using pandas ranking with pure PATSTAT data"""
        try:
            # Create subquery for medical applications with applicant data
            medical_apps_subquery = self.db.query(
                TLS201_APPLN.appln_id.label('appln_id'),
                self._get_ipc_class_case_statement(),
                TLS206_PERSON.person_name.label('applicant_name')
            ).join(
                TLS209_APPLN_IPC, TLS201_APPLN.appln_id == TLS209_APPLN_IPC.appln_id
            ).outerjoin(
                TLS207_PERS_APPLN, and_(
                    TLS201_APPLN.appln_id == TLS207_PERS_APPLN.appln_id,
                    TLS207_PERS_APPLN.applt_seq_nr > 0,  # Applicants only
                    TLS207_PERS_APPLN.invt_seq_nr == 0   # Not inventors
                )
            ).outerjoin(
                TLS206_PERSON, TLS207_PERS_APPLN.person_id == TLS206_PERSON.person_id
            ).filter(
                and_(
                    TLS201_APPLN.appln_filing_year.between(start_year, end_year),
                    TLS201_APPLN.appln_auth == 'EP',
                    self._get_ipc_class_filter()
                )
            ).distinct().subquery()

            # Get aggregated counts - pure PATSTAT data only
            results = self.db.query(
                medical_apps_subquery.c.ipc_class,
                medical_apps_subquery.c.applicant_name,
                func.count(func.distinct(medical_apps_subquery.c.appln_id)).label('app_count')
            ).filter(
                and_(
                    medical_apps_subquery.c.ipc_class.isnot(None),
                    medical_apps_subquery.c.applicant_name.isnot(None)
                )
            ).group_by(
                medical_apps_subquery.c.ipc_class,
                medical_apps_subquery.c.applicant_name
            ).all()

            # Convert to DataFrame and rank using pandas (no mock data)
            df = pd.DataFrame(results, columns=['ipc_class', 'applicant_name', 'app_count'])
            df['rank'] = df.groupby('ipc_class')['app_count'].rank(method='dense', ascending=False).astype(int)
            df = df[df['rank'] <= top_n].sort_values(['ipc_class', 'rank'])

            # Add class descriptions
            df['ipc_class_description'] = df['ipc_class'].map(self.MEDICAL_IPC_CLASSES)

            print(f"✅ Found top applicants across {df['ipc_class'].nunique()} IPC classes using pure PATSTAT data")
            return df

        except Exception as e:
            print(f"❌ Error in pandas ranking method: {e}")
            raise

    def _query_top_applicants_by_class_fallback(self, top_n: int, start_year: int, end_year: int) -> pd.DataFrame:
        """Fallback method using Python ranking instead of SQL window functions"""
        print("🔄 Using fallback method for top applicants query...")

        # Get all applicant counts first
        medical_apps_subquery = self.db.query(
            TLS201_APPLN.appln_id.label('appln_id'),
            self._get_ipc_class_case_statement(),
            TLS206_PERSON.person_name.label('applicant_name')
        ).join(
            TLS209_APPLN_IPC, TLS201_APPLN.appln_id == TLS209_APPLN_IPC.appln_id
        ).outerjoin(
            TLS207_PERS_APPLN, and_(
                TLS201_APPLN.appln_id == TLS207_PERS_APPLN.appln_id,
                TLS207_PERS_APPLN.applt_seq_nr > 0,
                TLS207_PERS_APPLN.invt_seq_nr == 0
            )
        ).outerjoin(
            TLS206_PERSON, TLS207_PERS_APPLN.person_id == TLS206_PERSON.person_id
        ).filter(
            and_(
                TLS201_APPLN.appln_filing_year.between(start_year, end_year),
                TLS201_APPLN.appln_auth == 'EP',
                self._get_ipc_class_filter()
            )
        ).distinct().subquery()

        results = self.db.query(
            medical_apps_subquery.c.ipc_class,
            medical_apps_subquery.c.applicant_name,
            func.count(func.distinct(medical_apps_subquery.c.appln_id)).label('app_count')
        ).filter(
            and_(
                medical_apps_subquery.c.ipc_class.isnot(None),
                medical_apps_subquery.c.applicant_name.isnot(None)
            )
        ).group_by(
            medical_apps_subquery.c.ipc_class,
            medical_apps_subquery.c.applicant_name
        ).all()

        # Convert to DataFrame and rank in Python
        df = pd.DataFrame(results, columns=['ipc_class', 'applicant_name', 'app_count'])
        df['rank'] = df.groupby('ipc_class')['app_count'].rank(method='dense', ascending=False).astype(int)
        df = df[df['rank'] <= top_n].sort_values(['ipc_class', 'rank'])

        # Add class descriptions
        df['ipc_class_description'] = df['ipc_class'].map(self.MEDICAL_IPC_CLASSES)

        return df

    def query_top_overall_applicants(self, top_n: int = 50, min_applications: int = 10,
                                   start_year: int = 2012, end_year: int = 2022) -> pd.DataFrame:
        """
        Query 4: Top N applicants across all 12 medical classes (2012-2022)
        Shows biggest players in medical technology with their diversification

        Args:
            top_n: Number of top applicants (default: 50)
            min_applications: Minimum applications threshold (default: 10)
            start_year: Start year for analysis (default: 2012)
            end_year: End year for analysis (default: 2022)

        Returns:
            DataFrame with columns: applicant_name, applicant_country, total_applications,
                                   different_classes, active_in_classes
        """
        print(f"🔍 Finding top {top_n} overall applicants across all medical classes ({start_year}-{end_year})...")

        try:
            # Create subquery for medical applications with full applicant data
            medical_apps_subquery = self.db.query(
                TLS201_APPLN.appln_id.label('appln_id'),
                self._get_ipc_class_case_statement(),
                TLS206_PERSON.person_name.label('applicant_name'),
                TLS206_PERSON.person_ctry_code.label('applicant_country')
            ).join(
                TLS209_APPLN_IPC, TLS201_APPLN.appln_id == TLS209_APPLN_IPC.appln_id
            ).outerjoin(
                TLS207_PERS_APPLN, and_(
                    TLS201_APPLN.appln_id == TLS207_PERS_APPLN.appln_id,
                    TLS207_PERS_APPLN.applt_seq_nr > 0,  # Applicants only
                    TLS207_PERS_APPLN.invt_seq_nr == 0   # Not inventors
                )
            ).outerjoin(
                TLS206_PERSON, TLS207_PERS_APPLN.person_id == TLS206_PERSON.person_id
            ).filter(
                and_(
                    TLS201_APPLN.appln_filing_year.between(start_year, end_year),
                    TLS201_APPLN.appln_auth == 'EP',
                    self._get_ipc_class_filter()
                )
            ).distinct().subquery()

            # Aggregate by applicant with class diversity metrics
            results = self.db.query(
                medical_apps_subquery.c.applicant_name,
                medical_apps_subquery.c.applicant_country,
                func.count(func.distinct(medical_apps_subquery.c.appln_id)).label('total_applications'),
                func.count(func.distinct(medical_apps_subquery.c.ipc_class)).label('different_classes')
            ).filter(
                medical_apps_subquery.c.applicant_name.isnot(None)
            ).group_by(
                medical_apps_subquery.c.applicant_name,
                medical_apps_subquery.c.applicant_country
            ).having(
                func.count(func.distinct(medical_apps_subquery.c.appln_id)) >= min_applications
            ).order_by(
                func.count(func.distinct(medical_apps_subquery.c.appln_id)).desc()
            ).limit(top_n).all()

            # Convert to DataFrame
            df = pd.DataFrame(results, columns=[
                'applicant_name', 'applicant_country', 'total_applications', 'different_classes'
            ])

            # Get active classes for each applicant (separate query due to string aggregation complexity)
            active_classes = {}
            for _, row in df.iterrows():
                applicant_name = row['applicant_name']

                classes_query = self.db.query(
                    func.distinct(medical_apps_subquery.c.ipc_class)
                ).filter(
                    and_(
                        medical_apps_subquery.c.applicant_name == applicant_name,
                        medical_apps_subquery.c.ipc_class.isnot(None)
                    )
                ).all()

                active_classes[applicant_name] = ', '.join(sorted([c[0] for c in classes_query if c[0]]))

            # Add active classes to DataFrame
            df['active_in_classes'] = df['applicant_name'].map(active_classes)

            print(f"✅ Found {len(df)} top applicants with {df['total_applications'].sum()} total applications")
            return df

        except Exception as e:
            print(f"❌ Error in top overall applicants query: {e}")
            raise

    def export_results_for_charts(self, output_dir: str = "./charts_data") -> Dict[str, str]:
        """
        Export all analysis results to CSV files for chart creation

        Args:
            output_dir: Directory to save CSV files (default: "./charts_data")

        Returns:
            Dictionary with file paths of exported data
        """
        import os

        print(f"📊 Exporting analysis results for chart creation...")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        files_created = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        try:
            # Export Query 2: Applications by year and class
            print("  📈 Exporting applications by year and class...")
            df_year_class = self.query_applications_by_year_and_class()
            file_1 = f"{output_dir}/medtech_ep_analysis_by_year_class_{timestamp}.csv"
            df_year_class.to_csv(file_1, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['applications_by_year_class'] = file_1

            # Export Query 3: Top applicants by class
            print("  🏆 Exporting top applicants by class...")
            df_top_by_class = self.query_top_applicants_by_class()
            file_2 = f"{output_dir}/medtech_ep_analysis_top_applicants_by_class_{timestamp}.csv"
            df_top_by_class.to_csv(file_2, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['top_applicants_by_class'] = file_2

            # Export Query 4: Top overall applicants
            print("  🥇 Exporting top overall applicants...")
            df_top_overall = self.query_top_overall_applicants()
            file_3 = f"{output_dir}/medtech_ep_analysis_top_overall_applicants_{timestamp}.csv"
            df_top_overall.to_csv(file_3, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['top_overall_applicants'] = file_3

            print(f"✅ All data exported successfully to {output_dir}")
            return files_created

        except Exception as e:
            print(f"❌ Error exporting results: {e}")
            raise

    def close(self):
        """Clean up connections"""
        try:
            if self.db:
                self.db.close()
                print("📤 Database session closed")

            if self.patstat:
                if hasattr(self.patstat, '_session') and self.patstat._session:
                    self.patstat._session.close()
                if hasattr(self.patstat, 'close_session'):
                    self.patstat.close_session()
                print("🔒 PATSTAT client closed")
        except Exception as e:
            print(f"⚠️ Cleanup warning (ignorable): {e}")
        finally:
            self.db = None
            self.patstat = None
            print("✨ All resources released")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup"""
        self.close()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_complete_analysis(output_dir: str = "./charts_data") -> Dict[str, str]:
    """
    Run complete medical patent analysis and export results for charting

    Args:
        output_dir: Directory to save CSV files

    Returns:
        Dictionary with file paths of exported data
    """
    print("=" * 80)
    print("🏥 MEDICAL PATENT ANALYSIS - EP APPLICATIONS (2012-2022)")
    print("=" * 80)
    print("📋 Analyzing 12 medical technology IPC classes:")

    analyzer = MedicalPatentAnalyzer()
    for ipc_class, description in analyzer.MEDICAL_IPC_CLASSES.items():
        print(f"   • {ipc_class:<8} {description}")

    print()

    with analyzer:
        return analyzer.export_results_for_charts(output_dir)


def get_medical_classes_info() -> Dict[str, str]:
    """Get information about the 12 medical technology IPC classes"""
    return MedicalPatentAnalyzer.MEDICAL_IPC_CLASSES


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting Medical Patent Analysis...")

    try:
        # Run complete analysis
        files = run_complete_analysis()

        print("\n" + "=" * 80)
        print("🎉 ANALYSIS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("📁 Files created for chart generation:")
        for analysis_type, file_path in files.items():
            print(f"   • {analysis_type}: {file_path}")

        print(f"\n💡 Next steps:")
        print(f"   📊 Use the CSV files to create charts in your preferred tool")
        print(f"   📈 Visualize trends by year and IPC class")
        print(f"   🏆 Analyze market leaders and competitive landscape")
        print(f"   🌍 Explore geographical distribution of applicants")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()