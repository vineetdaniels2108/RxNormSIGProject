import pandas as pd
from ydata_profiling import ProfileReport
import json

def create_medication_profile():
    """Create an interactive HTML report of the medication data."""
    
    print("📊 Creating interactive data profile...")
    
    # Load the enhanced medication table
    df = pd.read_csv('data/medication_table_with_sigs.csv', dtype={'rxcui': str})
    
    # Prepare data for profiling (convert JSON column to string length)
    df_profile = df.copy()
    df_profile['sig_count'] = df_profile['sig_instructions_json'].apply(
        lambda x: len(json.loads(x)) if x else 0
    )
    
    # Drop the JSON column for cleaner profiling
    df_profile = df_profile.drop(['sig_instructions_json', 'sig_instructions'], axis=1)
    
    # Create profile report
    profile = ProfileReport(
        df_profile, 
        title="RxNorm Medication Database Profile",
        explorative=True,
        dark_mode=False
    )
    
    # Save HTML report
    output_path = 'reports/medication_profile.html'
    profile.to_file(output_path)
    
    print(f"✅ Interactive profile saved to: {output_path}")
    print("🌐 Open this file in your browser to explore the data interactively!")
    
    return profile

if __name__ == "__main__":
    import os
    os.makedirs('reports', exist_ok=True)
    create_medication_profile() 