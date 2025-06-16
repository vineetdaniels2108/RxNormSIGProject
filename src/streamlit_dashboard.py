import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
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
    
    # Add data completeness columns
    df['has_dose_form'] = df['dose_form'].notna() & (df['dose_form'] != '')
    df['has_strength'] = df['available_strength'].notna() & (df['available_strength'] != '')
    df['has_sig'] = df['sig_count'] > 0
    
    # Count filled columns (using cleaned columns if available, otherwise original)
    drug_name_col = 'drug_name_clean' if 'drug_name_clean' in df.columns else 'drug_name'
    dose_form_col = 'dose_form_clean' if 'dose_form_clean' in df.columns else 'dose_form'
    strength_col = 'available_strength_clean' if 'available_strength_clean' in df.columns else 'available_strength'
    
    key_columns = [drug_name_col, 'term_type', dose_form_col, strength_col, 'sig_primary']
    df['filled_columns'] = 0
    for col in key_columns:
        df['filled_columns'] += (df[col].notna() & (df[col] != '')).astype(int)
    
    df['completeness_percent'] = (df['filled_columns'] / len(key_columns)) * 100
    
    # Categorize completeness
    df['completeness_category'] = pd.cut(
        df['completeness_percent'], 
        bins=[0, 40, 60, 80, 100], 
        labels=['Low (0-40%)', 'Medium (40-60%)', 'High (60-80%)', 'Complete (80-100%)'],
        include_lowest=True
    )
    
    # Use cleaned columns for display if available
    if 'drug_name_clean' in df.columns:
        df['display_drug_name'] = df['drug_name_clean']
    else:
        df['display_drug_name'] = df['drug_name']
        
    if 'dose_form_clean' in df.columns:
        df['display_dose_form'] = df['dose_form_clean']
    else:
        df['display_dose_form'] = df['dose_form']
        
    if 'available_strength_clean' in df.columns:
        df['display_strength'] = df['available_strength_clean']
    else:
        df['display_strength'] = df['available_strength']
    
    return df

def data_completeness_tab(df, filtered_df):
    """Data completeness analysis tab."""
    st.header("📊 Data Completeness Analysis")
    
    # Overall completeness metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        complete_records = len(filtered_df[filtered_df['filled_columns'] == 5])
        st.metric("Complete Records", f"{complete_records:,}", 
                 f"{(complete_records/len(filtered_df)*100):.1f}%")
    
    with col2:
        has_dose_form = filtered_df['has_dose_form'].sum()
        st.metric("Has Dose Form", f"{has_dose_form:,}", 
                 f"{(has_dose_form/len(filtered_df)*100):.1f}%")
    
    with col3:
        has_strength = filtered_df['has_strength'].sum()
        st.metric("Has Strength", f"{has_strength:,}", 
                 f"{(has_strength/len(filtered_df)*100):.1f}%")
    
    with col4:
        avg_completeness = filtered_df['completeness_percent'].mean()
        st.metric("Avg Completeness", f"{avg_completeness:.1f}%")
    
    # Completeness visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Completeness Distribution")
        completeness_counts = filtered_df['completeness_category'].value_counts()
        fig1 = px.pie(
            values=completeness_counts.values,
            names=completeness_counts.index,
            title="Records by Completeness Level",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("📊 Column-wise Completeness")
        columns_analysis = {
            'Drug Name': (filtered_df['drug_name'].notna() & (filtered_df['drug_name'] != '')).sum(),
            'Term Type': (filtered_df['term_type'].notna() & (filtered_df['term_type'] != '')).sum(),
            'Dose Form': filtered_df['has_dose_form'].sum(),
            'Strength': filtered_df['has_strength'].sum(),
            'SIG Primary': (filtered_df['sig_primary'].notna() & (filtered_df['sig_primary'] != '')).sum()
        }
        
        total_records = len(filtered_df)
        completeness_pct = {k: (v/total_records)*100 for k, v in columns_analysis.items()}
        
        fig2 = px.bar(
            x=list(completeness_pct.keys()),
            y=list(completeness_pct.values()),
            title="Completeness by Column (%)",
            color=list(completeness_pct.values()),
            color_continuous_scale="RdYlGn"
        )
        fig2.update_layout(showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)
    
    # Detailed completeness analysis
    st.subheader("🔍 Detailed Completeness Analysis")
    
    # Completeness heatmap by term type
    completeness_by_type = filtered_df.groupby('term_type').agg({
        'has_dose_form': 'mean',
        'has_strength': 'mean',
        'has_sig': 'mean'
    }) * 100
    
    fig3 = px.imshow(
        completeness_by_type.T,
        title="Data Completeness Heatmap by Term Type (%)",
        color_continuous_scale="RdYlGn",
        aspect="auto"
    )
    fig3.update_layout(
        xaxis_title="Term Type",
        yaxis_title="Data Fields"
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    # Missing data patterns
    st.subheader("🕳️ Missing Data Patterns")
    
    # Create missing data combinations
    missing_patterns = filtered_df.groupby(['has_dose_form', 'has_strength']).size().reset_index(name='count')
    missing_patterns['pattern'] = missing_patterns.apply(
        lambda x: f"Dose Form: {'✓' if x['has_dose_form'] else '✗'}, Strength: {'✓' if x['has_strength'] else '✗'}", 
        axis=1
    )
    
    fig4 = px.bar(
        missing_patterns,
        x='pattern',
        y='count',
        title="Common Missing Data Patterns",
        color='count',
        color_continuous_scale="Blues"
    )
    fig4.update_xaxes(tickangle=45)
    st.plotly_chart(fig4, use_container_width=True)

def quality_filters_tab(df):
    """Advanced filtering tab for data quality analysis."""
    st.header("🎯 Data Quality Filters")
    
    # Advanced filters
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Completeness Filters")
        
        # Completeness level filter
        completeness_filter = st.selectbox(
            "Completeness Level",
            ['All', 'Complete (80-100%)', 'High (60-80%)', 'Medium (40-60%)', 'Low (0-40%)']
        )
        
        # Missing data filters
        show_missing_dose = st.checkbox("Show only missing dose form")
        show_missing_strength = st.checkbox("Show only missing strength")
        show_missing_sig = st.checkbox("Show only missing SIG")
        
        # Column count filter
        min_filled_cols = st.slider("Minimum filled columns", 0, 5, 0)
    
    with col2:
        st.subheader("🔢 Data Range Filters")
        
        # SIG count filter
        sig_range = st.slider(
            "SIG instruction count range",
            min_value=int(df['sig_count'].min()),
            max_value=int(df['sig_count'].max()),
            value=(int(df['sig_count'].min()), int(df['sig_count'].max()))
        )
        
        # Drug name length filter (proxy for complexity)
        name_length_range = st.slider(
            "Drug name length range",
            min_value=int(df['drug_name'].str.len().min()),
            max_value=int(df['drug_name'].str.len().max()),
            value=(int(df['drug_name'].str.len().min()), int(df['drug_name'].str.len().max()))
        )
    
    # Apply advanced filters
    filtered_df = df.copy()
    
    # Completeness filter
    if completeness_filter != 'All':
        if completeness_filter == 'Complete (80-100%)':
            filtered_df = filtered_df[filtered_df['completeness_percent'] >= 80]
        elif completeness_filter == 'High (60-80%)':
            filtered_df = filtered_df[(filtered_df['completeness_percent'] >= 60) & (filtered_df['completeness_percent'] < 80)]
        elif completeness_filter == 'Medium (40-60%)':
            filtered_df = filtered_df[(filtered_df['completeness_percent'] >= 40) & (filtered_df['completeness_percent'] < 60)]
        elif completeness_filter == 'Low (0-40%)':
            filtered_df = filtered_df[filtered_df['completeness_percent'] < 40]
    
    # Missing data filters
    if show_missing_dose:
        filtered_df = filtered_df[~filtered_df['has_dose_form']]
    if show_missing_strength:
        filtered_df = filtered_df[~filtered_df['has_strength']]
    if show_missing_sig:
        filtered_df = filtered_df[filtered_df['sig_count'] == 0]
    
    # Range filters
    filtered_df = filtered_df[filtered_df['filled_columns'] >= min_filled_cols]
    filtered_df = filtered_df[
        (filtered_df['sig_count'] >= sig_range[0]) & 
        (filtered_df['sig_count'] <= sig_range[1])
    ]
    filtered_df = filtered_df[
        (filtered_df['drug_name'].str.len() >= name_length_range[0]) & 
        (filtered_df['drug_name'].str.len() <= name_length_range[1])
    ]
    
    # Display filtered results
    st.subheader(f"📊 Filtered Results ({len(filtered_df):,} medications)")
    
    if len(filtered_df) > 0:
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_completeness = filtered_df['completeness_percent'].mean()
            st.metric("Avg Completeness", f"{avg_completeness:.1f}%")
        
        with col2:
            complete_count = len(filtered_df[filtered_df['filled_columns'] == 5])
            st.metric("Complete Records", f"{complete_count:,}")
        
        with col3:
            avg_sigs = filtered_df['sig_count'].mean()
            st.metric("Avg SIGs", f"{avg_sigs:.1f}")
        
        with col4:
            unique_forms = filtered_df['dose_form'].nunique()
            st.metric("Unique Dose Forms", f"{unique_forms:,}")
        
        # Sample data preview
        st.subheader("📋 Sample Data Preview")
        preview_cols = [
            'drug_name', 'term_type', 'dose_form', 'available_strength', 
            'sig_primary', 'filled_columns', 'completeness_percent'
        ]
        
        sample_df = filtered_df[preview_cols].head(20).copy()
        sample_df['completeness_percent'] = sample_df['completeness_percent'].round(1)
        
        st.dataframe(sample_df, use_container_width=True)
        
        # Download filtered results
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data",
            data=csv,
            file_name=f"quality_filtered_medications.csv",
            mime="text/csv"
        )
    else:
        st.warning("No medications match the selected filters.")
    
    return filtered_df

def main_dashboard_tab(df, filtered_df):
    """Main dashboard with overview statistics."""
    st.header("💊 Medication Database Overview")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Medications", f"{len(filtered_df):,}")
    with col2:
        dose_form_col = 'display_dose_form' if 'dose_form_clean' in filtered_df.columns else 'dose_form'
        st.metric("Dose Forms", f"{filtered_df[dose_form_col].nunique():,}")
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
        dose_form_col = 'display_dose_form' if 'dose_form_clean' in filtered_df.columns else 'dose_form'
        dose_counts = filtered_df[dose_form_col].value_counts().head(10)
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

def search_tab(filtered_df):
    """Search and detailed view tab."""
    st.header("🔍 Search & Detailed View")
    
    # Enhanced search functionality
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_term = st.text_input("Search by medication name, dose form, or strength:")
    
    with col2:
        search_mode = st.selectbox("Search in:", ["All fields", "Drug name only", "Dose form only"])
    
    if search_term:
        # Enhanced search using multiple fields and cleaned data
        search_term_lower = search_term.lower()
        
        if search_mode == "All fields":
            # Search in multiple fields including searchable_text if available
            if 'searchable_text' in filtered_df.columns:
                search_mask = filtered_df['searchable_text'].str.contains(search_term_lower, case=False, na=False)
            else:
                search_mask = (
                    filtered_df['display_drug_name'].str.contains(search_term, case=False, na=False) |
                    filtered_df['display_dose_form'].str.contains(search_term, case=False, na=False) |
                    filtered_df['display_strength'].str.contains(search_term, case=False, na=False)
                )
        elif search_mode == "Drug name only":
            search_mask = filtered_df['display_drug_name'].str.contains(search_term, case=False, na=False)
        else:  # Dose form only
            search_mask = filtered_df['display_dose_form'].str.contains(search_term, case=False, na=False)
        
        search_results = filtered_df[search_mask]
        st.write(f"Found {len(search_results)} medications containing '{search_term}':")
        
        # Display results with cleaned data
        for idx, row in search_results.head(10).iterrows():
            with st.expander(f"💊 {row['display_drug_name']} ({row['term_type']}) - {row['completeness_percent']:.0f}% complete"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**RXCUI:** {row['rxcui']}")
                    if pd.notna(row['display_dose_form']) and str(row['display_dose_form']) != 'nan':
                        st.write(f"**Dose Form:** {row['display_dose_form']}")
                    if pd.notna(row['display_strength']) and str(row['display_strength']) != 'nan':
                        st.write(f"**Strength:** {row['display_strength']}")
                    st.write(f"**Data Completeness:** {row['completeness_percent']:.1f}% ({row['filled_columns']}/5 fields)")
                    
                    # Show search keywords if available
                    if 'search_keywords' in row and pd.notna(row['search_keywords']):
                        try:
                            keywords = eval(row['search_keywords']) if isinstance(row['search_keywords'], str) else row['search_keywords']
                            if keywords:
                                st.write(f"**Search Keywords:** {', '.join(keywords[:5])}{'...' if len(keywords) > 5 else ''}")
                        except:
                            pass
                
                with col2:
                    st.write(f"**Primary SIG:** {row['sig_primary']}")
                    
                    # Show all SIG options
                    if row['sig_instructions_json']:
                        sigs = json.loads(row['sig_instructions_json'])
                        st.write(f"**All SIG Options ({len(sigs)}):**")
                        for i, sig in enumerate(sigs, 1):
                            st.write(f"{i}. {sig}")
    
    # Data table with completeness info
    st.subheader("📋 Medication Data Table")
    
    # Select columns to display (use cleaned columns if available)
    available_cols = ['rxcui', 'display_drug_name', 'term_type', 'display_dose_form', 'display_strength', 
                     'sig_primary', 'sig_count', 'filled_columns', 'completeness_percent']
    
    # Add original columns if cleaned ones don't exist
    if 'drug_name_clean' not in filtered_df.columns:
        available_cols = [col.replace('display_', '') for col in available_cols]
    
    # Add search keywords if available
    if 'search_keywords' in filtered_df.columns:
        available_cols.append('search_keywords')
    
    display_cols = st.multiselect(
        "Select columns to display:",
        options=available_cols,
        default=['display_drug_name', 'term_type', 'display_dose_form', 'display_strength', 
                'sig_primary', 'completeness_percent'] if 'drug_name_clean' in filtered_df.columns else
                ['drug_name', 'term_type', 'dose_form', 'available_strength', 
                'sig_primary', 'completeness_percent']
    )
    
    if display_cols:
        display_df = filtered_df[display_cols].head(100).copy()
        if 'completeness_percent' in display_cols:
            display_df['completeness_percent'] = display_df['completeness_percent'].round(1)
        
        st.dataframe(display_df, use_container_width=True)

def main():
    st.title("💊 RxNorm Medication Database Explorer")
    st.markdown("Interactive dashboard for exploring 74,521+ medications with SIG instructions and data quality analysis")
    
    # Load data
    df = load_data()
    
    # Sidebar filters
    st.sidebar.header("🔍 Basic Filters")
    
    # Term type filter
    term_types = ['All'] + list(df['term_type'].unique())
    selected_term_type = st.sidebar.selectbox("Term Type", term_types)
    
    # Dose form filter (use cleaned data if available)
    dose_form_col = 'display_dose_form' if 'dose_form_clean' in df.columns else 'dose_form'
    dose_forms = df[dose_form_col].dropna().unique()
    dose_forms = ['All'] + sorted([form for form in dose_forms if form and str(form) != 'nan'])
    selected_dose_form = st.sidebar.selectbox("Dose Form", dose_forms)
    
    # Apply basic filters
    filtered_df = df.copy()
    if selected_term_type != 'All':
        filtered_df = filtered_df[filtered_df['term_type'] == selected_term_type]
    if selected_dose_form != 'All':
        filtered_df = filtered_df[filtered_df[dose_form_col] == selected_dose_form]
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Overview", 
        "🔍 Data Completeness", 
        "🎯 Quality Filters", 
        "🔎 Search & Details"
    ])
    
    with tab1:
        main_dashboard_tab(df, filtered_df)
    
    with tab2:
        data_completeness_tab(df, filtered_df)
    
    with tab3:
        quality_filtered_df = quality_filters_tab(df)
    
    with tab4:
        search_tab(filtered_df)
    
    # Download section (always visible)
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Download Data")
    
    # Download filtered data
    csv = filtered_df.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 Download Current View",
        data=csv,
        file_name=f"filtered_medications_{selected_term_type}_{selected_dose_form}.csv",
        mime="text/csv"
    )
    
    # Export SIG instructions
    if len(filtered_df) > 0:
        sig_export = []
        for idx, row in filtered_df.iterrows():
            if row['sig_instructions_json']:
                sigs = json.loads(row['sig_instructions_json'])
                for sig in sigs:
                    sig_export.append({
                        'rxcui': row['rxcui'],
                        'drug_name': row['drug_name'],
                        'sig_instruction': sig
                    })
        
        if sig_export:
            sig_df = pd.DataFrame(sig_export)
            sig_csv = sig_df.to_csv(index=False)
            st.sidebar.download_button(
                label="📋 Download SIG Instructions",
                data=sig_csv,
                file_name="all_sig_instructions.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main() 