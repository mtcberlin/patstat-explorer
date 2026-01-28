"""
Medical Patent Analysis Comparison: Global (TLS) vs Register (REG)
================================================================

Compare medical patent analysis results between Global tables (TLS) and Register tables (REG)
to identify differences in data coverage, quality, and insights.

Author: Claude Code with Arne Krueger, mtc, 2025
Based on: medical_patent_analysis.py and medical_patent_analysis_register.py
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Import both analyzers
from medtech_ep_analysis import MedicalPatentAnalyzer
from medtech_register_analysis import MedicalPatentAnalyzerRegister


class MedicalPatentComparison:
    """Compare medical patent analysis results between Global and Register data"""

    def __init__(self):
        """Initialize both analyzers"""
        print("🔗 Initializing Global (TLS) and Register (REG) analyzers...")
        self.global_analyzer = MedicalPatentAnalyzer()
        self.register_analyzer = MedicalPatentAnalyzerRegister()
        print("✅ Both analyzers initialized successfully")

    def compare_total_applications(self, start_year: int = 2012, end_year: int = 2022) -> Dict[str, Any]:
        """
        Compare total application counts between Global and Register data

        Returns:
            Dictionary with comparison statistics
        """
        print(f"🔍 Comparing total application counts ({start_year}-{end_year})...")

        try:
            # Get data from both sources
            global_data = self.global_analyzer.query_applications_by_year_and_class(start_year, end_year)
            register_data = self.register_analyzer.query_applications_by_year_and_class(start_year, end_year)

            # Calculate totals
            global_total = global_data['application_count'].sum()
            register_total = register_data['application_count'].sum()

            # Calculate year-by-year comparison
            global_by_year = global_data.groupby('appln_filing_year')['application_count'].sum()
            register_by_year = register_data.groupby('appln_filing_year')['application_count'].sum()

            year_comparison = pd.DataFrame({
                'year': range(start_year, end_year + 1),
                'global_count': [global_by_year.get(year, 0) for year in range(start_year, end_year + 1)],
                'register_count': [register_by_year.get(year, 0) for year in range(start_year, end_year + 1)]
            })
            year_comparison['difference'] = year_comparison['register_count'] - year_comparison['global_count']
            year_comparison['ratio'] = (year_comparison['register_count'] / year_comparison['global_count']).round(3)

            # Class-by-class comparison
            global_by_class = global_data.groupby('ipc_class')['application_count'].sum()
            register_by_class = register_data.groupby('ipc_class')['application_count'].sum()

            all_classes = sorted(set(global_by_class.index) | set(register_by_class.index))
            class_comparison = pd.DataFrame({
                'ipc_class': all_classes,
                'global_count': [global_by_class.get(cls, 0) for cls in all_classes],
                'register_count': [register_by_class.get(cls, 0) for cls in all_classes]
            })
            class_comparison['difference'] = class_comparison['register_count'] - class_comparison['global_count']
            class_comparison['ratio'] = (class_comparison['register_count'] / class_comparison['global_count']).round(3)

            # Add class descriptions
            class_comparison['description'] = class_comparison['ipc_class'].map(
                self.global_analyzer.MEDICAL_IPC_CLASSES
            )

            comparison_stats = {
                'global_total': global_total,
                'register_total': register_total,
                'total_difference': register_total - global_total,
                'total_ratio': round(register_total / global_total, 3) if global_total > 0 else 0,
                'year_comparison': year_comparison,
                'class_comparison': class_comparison,
                'period': f"{start_year}-{end_year}"
            }

            print(f"✅ Global total: {global_total:,} applications")
            print(f"✅ Register total: {register_total:,} applications")
            print(f"📊 Ratio (Register/Global): {comparison_stats['total_ratio']:.3f}")

            return comparison_stats

        except Exception as e:
            print(f"❌ Error in total applications comparison: {e}")
            raise

    def compare_top_applicants(self, top_n: int = 20, start_year: int = 2012, end_year: int = 2022) -> Dict[str, Any]:
        """
        Compare top applicants between Global and Register data

        Returns:
            Dictionary with applicant comparison data
        """
        print(f"🏆 Comparing top {top_n} overall applicants ({start_year}-{end_year})...")

        try:
            # Get top applicants from both sources
            global_applicants = self.global_analyzer.query_top_overall_applicants(top_n, 10, start_year, end_year)
            register_applicants = self.register_analyzer.query_top_overall_applicants(top_n, 10, start_year, end_year)

            # Create comparison DataFrame
            global_apps_dict = dict(zip(global_applicants['applicant_name'], global_applicants['total_applications']))
            register_apps_dict = dict(zip(register_applicants['applicant_name'], register_applicants['total_applications']))

            # Get all unique applicants
            all_applicants = sorted(set(global_apps_dict.keys()) | set(register_apps_dict.keys()))

            applicant_comparison = pd.DataFrame({
                'applicant_name': all_applicants,
                'global_count': [global_apps_dict.get(name, 0) for name in all_applicants],
                'register_count': [register_apps_dict.get(name, 0) for name in all_applicants]
            })

            applicant_comparison['difference'] = applicant_comparison['register_count'] - applicant_comparison['global_count']
            applicant_comparison['in_global'] = applicant_comparison['global_count'] > 0
            applicant_comparison['in_register'] = applicant_comparison['register_count'] > 0
            applicant_comparison['in_both'] = applicant_comparison['in_global'] & applicant_comparison['in_register']

            # Calculate statistics
            only_in_global = applicant_comparison[applicant_comparison['in_global'] & ~applicant_comparison['in_register']]
            only_in_register = applicant_comparison[~applicant_comparison['in_global'] & applicant_comparison['in_register']]
            in_both = applicant_comparison[applicant_comparison['in_both']]

            comparison_stats = {
                'applicant_comparison': applicant_comparison.sort_values('global_count', ascending=False),
                'total_unique_applicants': len(all_applicants),
                'only_in_global': len(only_in_global),
                'only_in_register': len(only_in_register),
                'in_both': len(in_both),
                'overlap_percentage': round(len(in_both) / len(all_applicants) * 100, 1) if all_applicants else 0,
                'global_top_applicants': global_applicants,
                'register_top_applicants': register_applicants
            }

            print(f"✅ Found {len(all_applicants)} unique applicants across both sources")
            print(f"📊 Only in Global: {len(only_in_global)}, Only in Register: {len(only_in_register)}, In both: {len(in_both)}")
            print(f"🎯 Overlap: {comparison_stats['overlap_percentage']:.1f}%")

            return comparison_stats

        except Exception as e:
            print(f"❌ Error in top applicants comparison: {e}")
            raise

    def compare_class_distribution(self, start_year: int = 2012, end_year: int = 2022) -> Dict[str, Any]:
        """
        Compare IPC class distribution between Global and Register data

        Returns:
            Dictionary with class distribution comparison
        """
        print(f"📈 Comparing IPC class distribution ({start_year}-{end_year})...")

        try:
            # Get data from both sources
            global_data = self.global_analyzer.query_applications_by_year_and_class(start_year, end_year)
            register_data = self.register_analyzer.query_applications_by_year_and_class(start_year, end_year)

            # Calculate class distributions
            global_class_dist = global_data.groupby('ipc_class')['application_count'].sum().sort_values(ascending=False)
            register_class_dist = register_data.groupby('ipc_class')['application_count'].sum().sort_values(ascending=False)

            # Create distribution comparison
            all_classes = sorted(set(global_class_dist.index) | set(register_class_dist.index))

            distribution_comparison = pd.DataFrame({
                'ipc_class': all_classes,
                'global_count': [global_class_dist.get(cls, 0) for cls in all_classes],
                'register_count': [register_class_dist.get(cls, 0) for cls in all_classes]
            })

            # Calculate percentages
            global_total = distribution_comparison['global_count'].sum()
            register_total = distribution_comparison['register_count'].sum()

            distribution_comparison['global_percentage'] = (distribution_comparison['global_count'] / global_total * 100).round(1)
            distribution_comparison['register_percentage'] = (distribution_comparison['register_count'] / register_total * 100).round(1)
            distribution_comparison['percentage_difference'] = (distribution_comparison['register_percentage'] - distribution_comparison['global_percentage']).round(1)

            # Add class descriptions
            distribution_comparison['description'] = distribution_comparison['ipc_class'].map(
                self.global_analyzer.MEDICAL_IPC_CLASSES
            )

            # Sort by global count for better readability
            distribution_comparison = distribution_comparison.sort_values('global_count', ascending=False)

            distribution_stats = {
                'distribution_comparison': distribution_comparison,
                'global_class_ranking': global_class_dist.index.tolist(),
                'register_class_ranking': register_class_dist.index.tolist(),
                'ranking_differences': self._calculate_ranking_differences(global_class_dist.index.tolist(), register_class_dist.index.tolist())
            }

            print(f"✅ Compared distribution across {len(all_classes)} IPC classes")

            return distribution_stats

        except Exception as e:
            print(f"❌ Error in class distribution comparison: {e}")
            raise

    def _calculate_ranking_differences(self, global_ranking: List[str], register_ranking: List[str]) -> Dict[str, int]:
        """Calculate ranking position differences for each class"""
        ranking_diff = {}

        for cls in set(global_ranking + register_ranking):
            global_pos = global_ranking.index(cls) + 1 if cls in global_ranking else None
            register_pos = register_ranking.index(cls) + 1 if cls in register_ranking else None

            if global_pos is not None and register_pos is not None:
                ranking_diff[cls] = register_pos - global_pos
            elif global_pos is not None:
                ranking_diff[cls] = f"Missing in Register (was #{global_pos} in Global)"
            elif register_pos is not None:
                ranking_diff[cls] = f"Only in Register (#{register_pos})"

        return ranking_diff

    def generate_comparison_report(self, output_dir: str = "./charts_data") -> Dict[str, str]:
        """
        Generate comprehensive comparison report and export CSV files

        Returns:
            Dictionary with file paths of exported comparison data
        """
        import os

        print("📊 Generating comprehensive Global vs Register comparison report...")

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        files_created = {}
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        try:
            # 1. Total applications comparison
            print("  📈 Analyzing total applications...")
            total_comparison = self.compare_total_applications()

            # Export year comparison
            year_file = f"{output_dir}/medtech_comparison_analysis_applications_by_year_{timestamp}.csv"
            total_comparison['year_comparison'].to_csv(year_file, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['year_comparison'] = year_file

            # Export class comparison
            class_file = f"{output_dir}/medtech_comparison_analysis_applications_by_class_{timestamp}.csv"
            total_comparison['class_comparison'].to_csv(class_file, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['class_comparison'] = class_file

            # 2. Top applicants comparison
            print("  🏆 Analyzing top applicants...")
            applicant_comparison = self.compare_top_applicants()

            # Export applicant comparison
            applicant_file = f"{output_dir}/medtech_comparison_analysis_top_applicants_{timestamp}.csv"
            applicant_comparison['applicant_comparison'].to_csv(applicant_file, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['applicant_comparison'] = applicant_file

            # 3. Class distribution comparison
            print("  📊 Analyzing class distribution...")
            distribution_comparison = self.compare_class_distribution()

            # Export distribution comparison
            distribution_file = f"{output_dir}/medtech_comparison_analysis_class_distribution_{timestamp}.csv"
            distribution_comparison['distribution_comparison'].to_csv(distribution_file, index=False, encoding='utf-8', sep=';', quoting=0)
            files_created['distribution_comparison'] = distribution_file

            # 4. Generate summary report
            print("  📝 Creating summary report...")
            summary_report = self._create_summary_report(total_comparison, applicant_comparison, distribution_comparison)

            summary_file = f"{output_dir}/medtech_comparison_analysis_summary_report_{timestamp}.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary_report)
            files_created['summary_report'] = summary_file

            print(f"✅ All comparison data exported successfully to {output_dir}")
            return files_created

        except Exception as e:
            print(f"❌ Error generating comparison report: {e}")
            raise

    def _create_summary_report(self, total_comp: Dict, applicant_comp: Dict, distribution_comp: Dict) -> str:
        """Create a comprehensive summary report"""

        report = f"""
================================================================================
MEDICAL PATENT ANALYSIS: GLOBAL (TLS) vs REGISTER (REG) COMPARISON REPORT
================================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Period: {total_comp['period']}

📊 EXECUTIVE SUMMARY
================================================================================
• Global (TLS) total applications: {total_comp['global_total']:,}
• Register (REG) total applications: {total_comp['register_total']:,}
• Difference: {total_comp['total_difference']:,} ({total_comp['total_ratio']:.1%} of Global)

🔍 KEY FINDINGS
================================================================================

1. DATA COVERAGE
   • Register data contains {total_comp['total_ratio']:.1%} of Global data applications
   • {'Register has MORE' if total_comp['total_difference'] > 0 else 'Register has FEWER'} applications than Global
   • Difference: {abs(total_comp['total_difference']):,} applications

2. APPLICANT OVERLAP
   • Total unique applicants: {applicant_comp['total_unique_applicants']}
   • Only in Global: {applicant_comp['only_in_global']}
   • Only in Register: {applicant_comp['only_in_register']}
   • In both sources: {applicant_comp['in_both']}
   • Overlap rate: {applicant_comp['overlap_percentage']:.1f}%

3. TOP IPC CLASSES (by Global data)
"""

        # Add top classes comparison
        top_classes = distribution_comp['distribution_comparison'].head(5)
        for _, row in top_classes.iterrows():
            report += f"   • {row['ipc_class']} ({row['description']})\n"
            report += f"     Global: {row['global_count']:,} ({row['global_percentage']:.1f}%) | Register: {row['register_count']:,} ({row['register_percentage']:.1f}%)\n"

        report += """
📈 YEAR-BY-YEAR TRENDS
================================================================================
"""

        # Add year trends
        year_data = total_comp['year_comparison']
        for _, row in year_data.iterrows():
            if row['global_count'] > 0:
                ratio = row['register_count'] / row['global_count']
                report += f"   {int(row['year'])}: Global {row['global_count']:,} | Register {row['register_count']:,} ({ratio:.1%})\n"

        report += f"""

🏆 TOP APPLICANTS COMPARISON
================================================================================
"""

        # Add top applicants from both sources
        report += "Global Top 5:\n"
        for i, (_, row) in enumerate(applicant_comp['global_top_applicants'].head(5).iterrows(), 1):
            report += f"   {i}. {row['applicant_name']}: {row['total_applications']} applications\n"

        report += "\nRegister Top 5:\n"
        for i, (_, row) in enumerate(applicant_comp['register_top_applicants'].head(5).iterrows(), 1):
            report += f"   {i}. {row['applicant_name']}: {row['total_applications']} applications\n"

        report += """

💡 RECOMMENDATIONS
================================================================================
• Use Global (TLS) data for comprehensive patent landscape analysis
• Use Register (REG) data for EP-specific procedural and legal status information
• Consider data source differences when comparing studies
• Register data appears to be a subset of Global data with different coverage patterns

================================================================================
"""

        return report

    def close(self):
        """Clean up both analyzers"""
        print("🔒 Closing analyzers...")
        try:
            self.global_analyzer.close()
            self.register_analyzer.close()
            print("✅ Both analyzers closed successfully")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with automatic cleanup"""
        self.close()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def run_complete_comparison(output_dir: str = "./charts_data") -> Dict[str, str]:
    """
    Run complete comparison between Global and Register medical patent data

    Args:
        output_dir: Directory to save comparison files

    Returns:
        Dictionary with file paths of exported comparison data
    """
    print("=" * 80)
    print("🔬 MEDICAL PATENT DATA COMPARISON: GLOBAL (TLS) vs REGISTER (REG)")
    print("=" * 80)

    with MedicalPatentComparison() as comparator:
        return comparator.generate_comparison_report(output_dir)


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting Global vs Register comparison analysis...")

    try:
        # Run complete comparison
        files = run_complete_comparison()

        print("\n" + "=" * 80)
        print("🎉 COMPARISON ANALYSIS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("📁 Files created for analysis:")
        for analysis_type, file_path in files.items():
            print(f"   • {analysis_type}: {file_path}")

        print(f"\n💡 Next steps:")
        print(f"   📊 Review the summary report for key insights")
        print(f"   📈 Analyze year-by-year and class-by-class differences")
        print(f"   🏆 Compare top applicant rankings between sources")
        print(f"   🔬 Consider data source selection for future analyses")

    except Exception as e:
        print(f"❌ Comparison analysis failed: {e}")
        import traceback
        traceback.print_exc()