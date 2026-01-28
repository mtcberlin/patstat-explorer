"""
Extended Medical Patent Analysis for PATSTAT BigQuery
===================================================

Enhanced analyzer for medical technology patents with jurisdiction comparisons.
Supports EP, DE, US, CN, and ALL PATSTAT jurisdictions for comprehensive analysis.

Author: Claude Code with Arne Krueger, mtc, 2025
Features: Jurisdiction comparisons, enhanced visualizations, chart-ready exports
"""

import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import warnings
warnings.filterwarnings('ignore')

# PATSTAT imports
from epo.tipdata.patstat import PatstatClient
from epo.tipdata.patstat.database.models import (
    TLS201_APPLN, TLS206_PERSON, TLS207_PERS_APPLN, TLS209_APPLN_IPC, TLS901_TECHN_FIELD_IPC
)
from sqlalchemy import func, text, case, and_, or_


class ExtendedMedicalPatentAnalyzer:
    """Enhanced analyzer for medical technology patents with jurisdiction comparisons"""

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
        'A61K': 'Medicinal Preparations (Drug Delivery)',
        'A61L': 'Sterilisation, Disinfection',
        'A61M': 'Devices for Introducing Media',
        'A61N': 'Electrotherapy, Magnetotherapy'
    }

    # Supported jurisdictions for analysis
    SUPPORTED_JURISDICTIONS = {
        'EP': 'European Patent Office',
        'DE': 'Germany (DPMA)',
        'US': 'United States (USPTO)',
        'CN': 'China (CNIPA)',
        'ALL': 'All PATSTAT jurisdictions'
    }

    def __init__(self):
        """Initialize PATSTAT connection"""
        self.patstat = None
        self.db = None
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
        #conditions.append(and_(
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
            if jurisdiction in self.SUPPORTED_JURISDICTIONS:
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
                                            jurisdictions: Union[str, List[str]] = ['EP']) -> pd.DataFrame:
        """
        Query: Applications by year and IPC class with jurisdiction support

        Args:
            start_year: Start year for analysis (default: 2012)
            end_year: End year for analysis (default: 2022)
            jurisdictions: Jurisdiction(s) to analyze (default: ['EP'])
                          Options: 'EP', 'DE', 'US', 'CN', 'ALL' or list of these

        Returns:
            DataFrame with columns: appln_filing_year, jurisdiction, ipc_class, application_count,
                                   ipc_class_description, jurisdiction_description
        """
        if isinstance(jurisdictions, str):
            jurisdictions = [jurisdictions]

        jurisdiction_str = ', '.join(jurisdictions)
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

            # Create subquery for medical applications
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

            # Main aggregation query
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

            # Add descriptions for better charts
            df['ipc_class_description'] = df['ipc_class'].map(self.MEDICAL_IPC_CLASSES)
            df['jurisdiction_description'] = df['jurisdiction'].map(self.SUPPORTED_JURISDICTIONS)

            print(f"✅ Found {len(df)} year/class/jurisdiction combinations with {df['application_count'].sum():,} total applications")
            return df

        except Exception as e:
            print(f"❌ Error in applications by year/class query: {e}")
            raise

    def query_top_applicants_by_class(self, top_n: int = 10, start_year: int = 2012, end_year: int = 2022,
                                     jurisdictions: Union[str, List[str]] = ['EP']) -> pd.DataFrame:
        """
        Query: Top N applicants per IPC class with jurisdiction support

        Args:
            top_n: Number of top applicants per class (default: 10)
            start_year: Start year for analysis (default: 2012)
            end_year: End year for analysis (default: 2022)
            jurisdictions: Jurisdiction(s) to analyze (default: ['EP'])

        Returns:
            DataFrame with columns: jurisdiction, ipc_class, applicant_name, app_count, rank,
                                   ipc_class_description, jurisdiction_description
        """
        if isinstance(jurisdictions, str):
            jurisdictions = [jurisdictions]

        jurisdiction_str = ', '.join(jurisdictions)
        print(f"🔍 Finding top {top_n} applicants per IPC class in {jurisdiction_str} ({start_year}-{end_year})...")

        try:
            # Get jurisdiction filter
            jurisdiction_filter = self._get_jurisdiction_filter(jurisdictions)

            # Build filter conditions
            filter_conditions = [
                TLS201_APPLN.appln_filing_year.between(start_year, end_year),
                self._get_ipc_class_filter()
            ]

            if jurisdiction_filter is not None:
                filter_conditions.append(jurisdiction_filter)

            # Create subquery for medical applications with applicant data
            medical_apps_subquery = self.db.query(
                TLS201_APPLN.appln_id.label('appln_id'),
                TLS201_APPLN.appln_auth.label('jurisdiction'),
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
                and_(*filter_conditions)
            ).distinct().subquery()

            # Get aggregated counts
            results = self.db.query(
                medical_apps_subquery.c.jurisdiction,
                medical_apps_subquery.c.ipc_class,
                medical_apps_subquery.c.applicant_name,
                func.count(func.distinct(medical_apps_subquery.c.appln_id)).label('app_count')
            ).filter(
                and_(
                    medical_apps_subquery.c.ipc_class.isnot(None),
                    medical_apps_subquery.c.applicant_name.isnot(None)
                )
            ).group_by(
                medical_apps_subquery.c.jurisdiction,
                medical_apps_subquery.c.ipc_class,
                medical_apps_subquery.c.applicant_name
            ).all()

            # Convert to DataFrame and rank using pandas
            df = pd.DataFrame(results, columns=['jurisdiction', 'ipc_class', 'applicant_name', 'app_count'])
            df['rank'] = df.groupby(['jurisdiction', 'ipc_class'])['app_count'].rank(method='dense', ascending=False).astype(int)
            df = df[df['rank'] <= top_n].sort_values(['jurisdiction', 'ipc_class', 'rank'])

            # Add descriptions
            df['ipc_class_description'] = df['ipc_class'].map(self.MEDICAL_IPC_CLASSES)
            df['jurisdiction_description'] = df['jurisdiction'].map(self.SUPPORTED_JURISDICTIONS)

            print(f"✅ Found top applicants across {df['ipc_class'].nunique()} IPC classes in {df['jurisdiction'].nunique()} jurisdiction(s)")
            return df

        except Exception as e:
            print(f"❌ Error in top applicants by class query: {e}")
            raise

    def query_top_overall_applicants(self, top_n: int = 50, min_applications: int = 10,
                                    start_year: int = 2012, end_year: int = 2022,
                                    jurisdictions: Union[str, List[str]] = ['EP']) -> pd.DataFrame:
        """
        Query: Top N overall applicants across all medical classes

        Args:
            top_n: Number of top applicants (default: 50)
            min_applications: Minimum applications threshold (default: 10)
            start_year: Start year for analysis (default: 2012)
            end_year: End year for analysis (default: 2022)
            jurisdictions: Jurisdiction(s) to analyze (default: ['EP'])

        Returns:
            DataFrame with columns: jurisdiction, applicant_name, applicant_country, total_applications,
                                   different_classes, active_in_classes, jurisdiction_description
        """
        if isinstance(jurisdictions, str):
            jurisdictions = [jurisdictions]

        jurisdiction_str = ', '.join(jurisdictions)
        print(f"🔍 Finding top {top_n} overall applicants in {jurisdiction_str} ({start_year}-{end_year})...")

        try:
            # Get jurisdiction filter
            jurisdiction_filter = self._get_jurisdiction_filter(jurisdictions)

            # Build filter conditions
            filter_conditions = [
                TLS201_APPLN.appln_filing_year.between(start_year, end_year),
                self._get_ipc_class_filter()
            ]

            if jurisdiction_filter is not None:
                filter_conditions.append(jurisdiction_filter)

            # Create subquery for medical applications with full applicant data
            medical_apps_subquery = self.db.query(
                TLS201_APPLN.appln_id.label('appln_id'),
                TLS201_APPLN.appln_auth.label('jurisdiction'),
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
                and_(*filter_conditions)
            ).distinct().subquery()

            # Aggregate by applicant
            results = self.db.query(
                medical_apps_subquery.c.jurisdiction,
                medical_apps_subquery.c.applicant_name,
                medical_apps_subquery.c.applicant_country,
                func.count(func.distinct(medical_apps_subquery.c.appln_id)).label('total_applications'),
                func.count(func.distinct(medical_apps_subquery.c.ipc_class)).label('different_classes')
            ).filter(
                medical_apps_subquery.c.applicant_name.isnot(None)
            ).group_by(
                medical_apps_subquery.c.jurisdiction,
                medical_apps_subquery.c.applicant_name,
                medical_apps_subquery.c.applicant_country
            ).having(
                func.count(func.distinct(medical_apps_subquery.c.appln_id)) >= min_applications
            ).order_by(
                func.count(func.distinct(medical_apps_subquery.c.appln_id)).desc()
            ).limit(top_n * len(jurisdictions)).all()  # Get more to ensure top_n per jurisdiction

            # Convert to DataFrame
            df = pd.DataFrame(results, columns=[
                'jurisdiction', 'applicant_name', 'applicant_country', 'total_applications', 'different_classes'
            ])

            # Get active classes for each applicant (simplified approach)
            df['active_in_classes'] = df.apply(lambda row: self._get_active_classes_for_applicant(
                row['applicant_name'], row['jurisdiction'], start_year, end_year), axis=1)

            # Add jurisdiction descriptions
            df['jurisdiction_description'] = df['jurisdiction'].map(self.SUPPORTED_JURISDICTIONS)

            # Ensure top_n per jurisdiction if multiple jurisdictions
            if len(jurisdictions) > 1:
                df = df.groupby('jurisdiction').head(top_n).reset_index(drop=True)

            print(f"✅ Found {len(df)} top applicants across {df['jurisdiction'].nunique()} jurisdiction(s)")
            return df

        except Exception as e:
            print(f"❌ Error in top overall applicants query: {e}")
            raise

    def _get_active_classes_for_applicant(self, applicant_name: str, jurisdiction: str,
                                         start_year: int, end_year: int) -> str:
        """Helper method to get active IPC classes for a specific applicant"""
        try:
            # Simplified query to get classes for applicant
            filter_conditions = [
                TLS201_APPLN.appln_filing_year.between(start_year, end_year),
                TLS201_APPLN.appln_auth == jurisdiction,
                self._get_ipc_class_filter()
            ]

            medical_apps = self.db.query(
                func.distinct(self._get_ipc_class_case_statement())
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
                    *filter_conditions,
                    TLS206_PERSON.person_name == applicant_name
                )
            ).all()

            classes = [c[0] for c in medical_apps if c[0]]
            return ', '.join(sorted(classes))

        except Exception:
            return "N/A"

    def compare_jurisdictions(self, jurisdictions: List[str] = ['EP', 'DE', 'US', 'CN'],
                             start_year: int = 2012, end_year: int = 2022) -> Dict[str, pd.DataFrame]:
        """
        Compare medical patent activities across multiple jurisdictions

        Args:
            jurisdictions: List of jurisdictions to compare (default: ['EP', 'DE', 'US', 'CN'])
            start_year: Start year for analysis (default: 2012)
            end_year: End year for analysis (default: 2022)

        Returns:
            Dictionary with comparison DataFrames for different analysis types
        """
        print(f"🔍 Comparing medical patent activities across {', '.join(jurisdictions)} ({start_year}-{end_year})...")

        comparison_results = {}

        try:
            # 1. Applications by year comparison
            print("  📊 Analyzing applications by year across jurisdictions...")
            year_comparison = self.query_applications_by_year_and_class(
                start_year=start_year, end_year=end_year, jurisdictions=jurisdictions
            )
            comparison_results['by_year'] = year_comparison

            # 2. Total applications by IPC class comparison
            print("  📊 Analyzing IPC class distribution across jurisdictions...")
            class_totals = year_comparison.groupby(['jurisdiction', 'ipc_class'])['application_count'].sum().reset_index()
            class_totals['ipc_class_description'] = class_totals['ipc_class'].map(self.MEDICAL_IPC_CLASSES)
            class_totals['jurisdiction_description'] = class_totals['jurisdiction'].map(self.SUPPORTED_JURISDICTIONS)
            comparison_results['by_class'] = class_totals

            # 3. Jurisdiction summary statistics
            print("  📊 Computing jurisdiction summary statistics...")
            summary = year_comparison.groupby('jurisdiction').agg({
                'application_count': ['sum', 'mean'],
                'ipc_class': 'nunique'
            }).round(2)
            summary.columns = ['total_applications', 'avg_per_year_class', 'active_ipc_classes']
            summary = summary.reset_index()
            summary['jurisdiction_description'] = summary['jurisdiction'].map(self.SUPPORTED_JURISDICTIONS)
            comparison_results['summary'] = summary

            print(f"✅ Jurisdiction comparison completed across {len(jurisdictions)} jurisdictions")
            return comparison_results

        except Exception as e:
            print(f"❌ Error in jurisdiction comparison: {e}")
            raise

    def export_all_analyses(self, output_dir: str = "./charts_data",
                           jurisdictions: List[str] = ['EP'],
                           start_year: int = 2012, end_year: int = 2022) -> Dict[str, str]:
        """
        Export all analysis results to CSV files for chart creation

        Args:
            output_dir: Directory to save CSV files (default: "./charts_data")
            jurisdictions: Jurisdictions to analyze (default: ['EP'])
            start_year: Start year for analysis (default: 2012)
            end_year: End year for analysis (default: 2022)

        Returns:
            Dictionary with file paths of exported data
        """
        import os

        print(f"📊 Exporting extended analysis results for {', '.join(jurisdictions)}...")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        files_created = {}

        try:
            # 1. Applications by year and class
            print("  📈 Exporting applications by year and class...")
            df_year_class = self.query_applications_by_year_and_class(
                start_year=start_year, end_year=end_year, jurisdictions=jurisdictions
            )
            file_1 = f"{output_dir}/medtech_multi_jurisdiction_applications_by_year_class_{timestamp}.csv"
            df_year_class.to_csv(file_1, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['applications_by_year_class'] = file_1

            # 2. Top applicants by class
            print("  🏆 Exporting top applicants by class...")
            df_top_by_class = self.query_top_applicants_by_class(
                start_year=start_year, end_year=end_year, jurisdictions=jurisdictions
            )
            file_2 = f"{output_dir}/medtech_multi_jurisdiction_top_applicants_by_class_{timestamp}.csv"
            df_top_by_class.to_csv(file_2, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['top_applicants_by_class'] = file_2

            # 3. Top overall applicants
            print("  🥇 Exporting top overall applicants...")
            df_top_overall = self.query_top_overall_applicants(
                start_year=start_year, end_year=end_year, jurisdictions=jurisdictions
            )
            file_3 = f"{output_dir}/medtech_multi_jurisdiction_top_overall_applicants_{timestamp}.csv"
            df_top_overall.to_csv(file_3, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['top_overall_applicants'] = file_3

            # 4. If multiple jurisdictions, create comparison
            if len(jurisdictions) > 1:
                print("  🌍 Exporting jurisdiction comparisons...")
                comparison_data = self.compare_jurisdictions(
                    jurisdictions=jurisdictions, start_year=start_year, end_year=end_year
                )

                for analysis_type, df in comparison_data.items():
                    file_path = f"{output_dir}/medtech_multi_jurisdiction_comparison_{analysis_type}_{timestamp}.csv"
                    df.to_csv(file_path, index=False, encoding='utf-8', sep=';', quoting=0)
                    files_created[f'comparison_{analysis_type}'] = file_path

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
# CONVENIENCE FUNCTIONS FOR EXTENDED ANALYSIS
# =============================================================================

def run_ep_vs_all_comparison(start_year: int = 2012, end_year: int = 2022,
                            output_dir: str = "./ep_vs_all_data") -> Dict[str, str]:
    """
    Compare EP medical patents vs ALL PATSTAT medical patents

    Args:
        start_year: Start year for analysis (default: 2012)
        end_year: End year for analysis (default: 2022)
        output_dir: Output directory for CSV files

    Returns:
        Dictionary with file paths of exported data
    """
    print("=" * 80)
    print("🏥 EP vs ALL PATSTAT - MEDICAL PATENT COMPARISON")
    print("=" * 80)

    with ExtendedMedicalPatentAnalyzer() as analyzer:
        return analyzer.export_all_analyses(
            output_dir=output_dir,
            jurisdictions=['EP', 'ALL'],
            start_year=start_year,
            end_year=end_year
        )


def run_major_jurisdictions_comparison(start_year: int = 2012, end_year: int = 2022,
                                     output_dir: str = "./major_jurisdictions_data") -> Dict[str, str]:
    """
    Compare medical patents across EP, DE, US, CN

    Args:
        start_year: Start year for analysis (default: 2012)
        end_year: End year for analysis (default: 2022)
        output_dir: Output directory for CSV files

    Returns:
        Dictionary with file paths of exported data
    """
    print("=" * 80)
    print("🌍 MAJOR JURISDICTIONS - MEDICAL PATENT COMPARISON")
    print("=" * 80)
    print("📋 Comparing: EP, DE, US, CN")

    with ExtendedMedicalPatentAnalyzer() as analyzer:
        return analyzer.export_all_analyses(
            output_dir=output_dir,
            jurisdictions=['EP', 'DE', 'US', 'CN'],
            start_year=start_year,
            end_year=end_year
        )


def get_supported_jurisdictions() -> Dict[str, str]:
    """Get information about supported jurisdictions"""
    return ExtendedMedicalPatentAnalyzer.SUPPORTED_JURISDICTIONS


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting Extended Medical Patent Analysis...")

    try:
        # Demo: Run EP analysis
        print("\n1️⃣ Running EP analysis...")
        with ExtendedMedicalPatentAnalyzer() as analyzer:
            files_ep = analyzer.export_all_analyses(
                jurisdictions=['EP'],
                start_year=2012,
                end_year=2022
            )

        # Demo: Run jurisdiction comparison
        print("\n2️⃣ Running major jurisdictions comparison...")
        files_comparison = run_major_jurisdictions_comparison(
            start_year=2012,
            end_year=2022
        )

        print("\n" + "=" * 80)
        print("🎉 EXTENDED ANALYSIS COMPLETED!")
        print("=" * 80)
        print("📁 Files created:")
        all_files = {**files_ep, **files_comparison}
        for analysis_type, file_path in all_files.items():
            print(f"   • {analysis_type}: {file_path}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()