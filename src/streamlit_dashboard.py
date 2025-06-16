import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from collections import Counter

# Page config
st.set_page_config(
    page_title="RxNorm Medication Database Explorer",
    page_icon="💊",
    layout="wide"
)

@st.cache_data
def load_data():
    """Load and cache the medication data."""
    df = pd.read_csv('data/medication_table_with_sigs.csv', dtype={'rxcui': str})
    
    # Parse SIG instructions
    df['sig_count'] = df['sig_instructions_json'].apply(
        lambda x: len(json.loads(x)) if x else 0
    )
    
    return df

def main():
    st.title("💊 RxNorm Medication Database Explorer")
    st.markdown("Interactive dashboard for exploring 74,521+ medications with SIG instructions")
    
    # Load data
    df = load_data()
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Term type filter
    term_types = ['All'] + list(df['term_type'].unique())
    selected_term_type = st.sidebar.selectbox("Term Type", term_types)
    
    # Dose form filter
    dose_forms = df['dose_form'].dropna().unique()
    dose_forms = ['All'] + [form for form in dose_forms if form and str(form) != 'nan']
    selected_dose_form = st.sidebar.selectbox("Dose Form", dose_forms)
    
    # Apply filters
    filtered_df = df.copy()
    if selected_term_type != 'All':
        filtered_df = filtered_df[filtered_df['term_type'] == selected_term_type]
    if selected_dose_form != 'All':
        filtered_df = filtered_df[filtered_df['dose_form'] == selected_dose_form]
    
    # Main dashboard
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Medications", f"{len(filtered_df):,}")
    with col2:
        st.metric("Dose Forms", f"{filtered_df['dose_form'].nunique():,}")
    with col3:
        avg_sigs = filtered_df['sig_count'].mean()
        st.metric("Avg SIGs per Med", f"{avg_sigs:.1f}")
    with col4:
        total_sigs = filtered_df['sig_count'].sum()
        st.metric("Total SIG Instructions", f"{total_sigs:,}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Medications by Term Type")
        term_counts = filtered_df['term_type'].value_counts()
        fig1 = px.pie(
            values=term_counts.values, 
            names=term_counts.index,
            title="Distribution by Term Type"
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("📈 Top Dose Forms")
        dose_counts = filtered_df['dose_form'].value_counts().head(10)
        fig2 = px.bar(
            x=dose_counts.values,
            y=dose_counts.index,
            orientation='h',
            title="Top 10 Dose Forms"
        )
        fig2.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)
    
    # SIG Analysis
    st.subheader("🧠 SIG Instructions Analysis")
    col1, col2 = st.columns(2)
    
    with col1:
        # SIG count distribution
        fig3 = px.histogram(
            filtered_df, 
            x='sig_count',
            title="Distribution of SIG Counts per Medication",
            nbins=20
        )
        st.plotly_chart(fig3, use_container_width=True)
    
    with col2:
        # Strength availability
        has_strength = filtered_df['available_strength'].notna().sum()
        no_strength = len(filtered_df) - has_strength
        
        fig4 = px.pie(
            values=[has_strength, no_strength],
            names=['Has Strength Info', 'No Strength Info'],
            title="Strength Information Availability"
        )
        st.plotly_chart(fig4, use_container_width=True)
    
    # Search functionality
    st.subheader("🔍 Search Medications")
    search_term = st.text_input("Search by medication name:")
    
    if search_term:
        search_results = filtered_df[
            filtered_df['drug_name'].str.contains(search_term, case=False, na=False)
        ]
        st.write(f"Found {len(search_results)} medications containing '{search_term}':")
        
        # Display results
        for idx, row in search_results.head(10).iterrows():
            with st.expander(f"💊 {row['drug_name']} ({row['term_type']})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**RXCUI:** {row['rxcui']}")
                    if row['dose_form'] and str(row['dose_form']) != 'nan':
                        st.write(f"**Dose Form:** {row['dose_form']}")
                    if row['available_strength'] and str(row['available_strength']) != 'nan':
                        st.write(f"**Strength:** {row['available_strength']}")
                
                with col2:
                    st.write(f"**Primary SIG:** {row['sig_primary']}")
                    
                    # Show all SIG options
                    if row['sig_instructions_json']:
                        sigs = json.loads(row['sig_instructions_json'])
                        st.write(f"**All SIG Options ({len(sigs)}):**")
                        for i, sig in enumerate(sigs, 1):
                            st.write(f"{i}. {sig}")
    
    # Data table
    st.subheader("📋 Medication Data Table")
    
    # Select columns to display
    display_cols = st.multiselect(
        "Select columns to display:",
        options=['rxcui', 'drug_name', 'term_type', 'dose_form', 'available_strength', 'sig_primary', 'sig_count'],
        default=['drug_name', 'term_type', 'dose_form', 'available_strength', 'sig_primary']
    )
    
    if display_cols:
        st.dataframe(
            filtered_df[display_cols].head(100),
            use_container_width=True
        )
    
    # Download section
    st.subheader("💾 Download Data")
    col1, col2 = st.columns(2)
    
    with col1:
        # Download filtered data
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv,
            file_name=f"filtered_medications_{selected_term_type}_{selected_dose_form}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export SIG instructions
        if len(filtered_df) > 0:
            sig_export = []
            for idx, row in filtered_df.iterrows():
                sigs = json.loads(row['sig_instructions_json'])
                for sig in sigs:
                    sig_export.append({
                        'rxcui': row['rxcui'],
                        'drug_name': row['drug_name'],
                        'sig_instruction': sig
                    })
            
            sig_df = pd.DataFrame(sig_export)
            sig_csv = sig_df.to_csv(index=False)
            st.download_button(
                label="Download All SIG Instructions",
                data=sig_csv,
                file_name="all_sig_instructions.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main() 