import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np
from collections import Counter

# Performance configuration
PERFORMANCE_CONFIG = {
    'max_search_results': 50,
    'max_table_rows': 100,
    'enable_lazy_loading': True,
    'cache_search_results': True
}

def optimize_dataframe(df):
    """Optimize DataFrame memory usage and performance."""
    # Convert string columns to category where beneficial
    categorical_columns = ['term_type', 'dose_form', 'dose_form_clean']
    for col in categorical_columns:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].astype('category')
    
    # Optimize string columns
    string_columns = ['drug_name', 'drug_name_clean', 'sig_primary']
    for col in string_columns:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].astype('string')
    
    return df

def create_performance_warning():
    """Display performance tips for large datasets."""
    with st.sidebar:
        with st.expander("⚡ Performance Tips"):
            st.markdown("""
            **For faster performance:**
            - Use specific search terms
            - Apply filters to reduce data size
            - Use pagination for large result sets
            - Clear browser cache if app feels slow
            
            **Current optimizations:**
            ✅ Data caching enabled
            ✅ Search result limiting
            ✅ Lazy loading for large datasets
            ✅ Optimized data types
            """)

# Page config
st.set_page_config(
    page_title="RxNorm Medication Database Explorer",
    page_icon="💊",
    layout="wide"
)

@st.cache_data(show_spinner="🔄 Loading enhanced medication database...")
def load_data():
    """Load and cache the enhanced medication data with NDC and brand name information."""
    # Read only essential columns initially to speed up loading
    essential_cols = [
        'rxcui', 'drug_name', 'term_type', 'dose_form', 'available_strength',
        'sig_primary', 'sig_instructions_json', 'ndc_primary', 'ndc_count',
        'major_pharma_primary', 'pharma_company_cleaned', 'labeler_primary', 
        'brand_searchable_text', 'enhanced_searchable_text', 'brand_drug_name_merged'
    ]
    
    # Try to read enhanced data v3 first, then v2, then v1, then cleaned, then original
    for filename in ['data/medication_table_with_sigs_enhanced_v3.csv',
                     'data/medication_table_with_sigs_enhanced_v2.csv',
                     'data/medication_table_with_sigs_enhanced.csv', 
                     'data/medication_table_with_sigs_cleaned.csv',
                     'data/medication_table_with_sigs.csv']:
        try:
            df = pd.read_csv(filename, 
                            dtype={'rxcui': str}, 
                            usecols=lambda x: x in essential_cols or 'clean' in x or x in [
                                'ndc_codes_json', 'labelers_json', 'major_pharma_json', 
                                'pharma_companies_json', 'pharma_company_cleaned',
                                'enhanced_searchable_text', 'brand_drug_name_merged',
                                'gpi_primary', 'gpi_count', 'search_keywords'
                            ])
            print(f"✅ Loaded data from: {filename}")
            break
        except Exception as e:
            print(f"⚠️ Could not load {filename}: {e}")
            continue
    else:
        raise FileNotFoundError("No medication data files found!")
    
    # Optimize JSON parsing - only count SIGs, don't parse all
    df['sig_count'] = df['sig_instructions_json'].apply(
        lambda x: x.count('",') + 1 if x and '"' in str(x) else 0
    )
    
    # Add data completeness columns efficiently
    df['has_dose_form'] = df['dose_form'].notna() & (df['dose_form'] != '')
    df['has_strength'] = df['available_strength'].notna() & (df['available_strength'] != '')
    df['has_sig'] = df['sig_count'] > 0
    df['has_ndc'] = df.get('ndc_count', pd.Series(0)) > 0
    df['has_pharma_company'] = df.get('pharma_company_cleaned', pd.Series()).notna()
    
    # Use cleaned columns if available, otherwise original
    drug_name_col = 'drug_name_clean' if 'drug_name_clean' in df.columns else 'drug_name'
    dose_form_col = 'dose_form_clean' if 'dose_form_clean' in df.columns else 'dose_form'
    strength_col = 'available_strength_clean' if 'available_strength_clean' in df.columns else 'available_strength'
    
    # Enhanced completeness calculation including new fields
    key_columns = [drug_name_col, 'term_type', dose_form_col, strength_col, 'sig_primary']
    df['filled_columns'] = sum((df[col].notna() & (df[col] != '')).astype(int) for col in key_columns)
    
    # Add bonus points for NDC and pharmaceutical company data
    if 'ndc_count' in df.columns:
        df['filled_columns'] += (df['ndc_count'] > 0).astype(int) * 0.5  # Half point for NDC
    if 'major_pharma_primary' in df.columns:
        df['filled_columns'] += df['major_pharma_primary'].notna().astype(int) * 0.5  # Half point for pharma company
    
    df['completeness_percent'] = (df['filled_columns'] / (len(key_columns) + 1)) * 100  # +1 for bonus points
    
    # Categorize completeness efficiently
    df['completeness_category'] = pd.cut(
        df['completeness_percent'], 
        bins=[0, 40, 60, 80, 100], 
        labels=['Low (0-40%)', 'Medium (40-60%)', 'High (60-80%)', 'Complete (80-100%)'],
        include_lowest=True
    )
    
    # Set display columns efficiently
    df['display_drug_name'] = df.get('drug_name_clean', df['drug_name'])
    df['display_dose_form'] = df.get('dose_form_clean', df['dose_form'])
    df['display_strength'] = df.get('available_strength_clean', df['available_strength'])
    
    # Apply performance optimizations
    df = optimize_dataframe(df)
    
    return df

@st.cache_data(show_spinner="🔍 Processing search results...")
def get_search_results(df, search_term, search_mode='all', max_results=None):
    """Optimized search function with caching and enhanced brand name support."""
    if not search_term.strip():
        return pd.DataFrame()
    
    search_term = search_term.lower().strip()
    
    # Create boolean masks for different search modes
    if search_mode == 'drug_name':
        mask = df['display_drug_name'].str.lower().str.contains(search_term, na=False)
    elif search_mode == 'dose_form':
        mask = df['display_dose_form'].str.lower().str.contains(search_term, na=False)
    elif search_mode == 'brand_name':
        # Search in pharmaceutical company fields using cleaned data
        enhanced_brand_mask = df.get('enhanced_searchable_text', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        brand_mask = df.get('brand_searchable_text', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        pharma_cleaned_mask = df.get('pharma_company_cleaned', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        pharma_mask = df.get('major_pharma_primary', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        labeler_mask = df.get('labeler_primary', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        mask = enhanced_brand_mask | brand_mask | pharma_cleaned_mask | pharma_mask | labeler_mask
    elif search_mode == 'ndc':
        # Search in NDC codes
        ndc_primary_mask = df.get('ndc_primary', pd.Series()).astype(str).str.contains(search_term, na=False)
        ndc_json_mask = df.get('ndc_codes_json', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        mask = ndc_primary_mask | ndc_json_mask
    else:  # 'all' mode - enhanced with brand name search
        # Search across multiple columns efficiently
        name_match = df['display_drug_name'].str.lower().str.contains(search_term, na=False)
        form_match = df['display_dose_form'].str.lower().str.contains(search_term, na=False)
        strength_match = df['display_strength'].astype(str).str.lower().str.contains(search_term, na=False)
        
        # Enhanced brand name search using cleaned and improved data
        enhanced_brand_match = df.get('enhanced_searchable_text', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        brand_match = df.get('brand_searchable_text', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        pharma_cleaned_match = df.get('pharma_company_cleaned', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        pharma_match = df.get('major_pharma_primary', pd.Series()).astype(str).str.lower().str.contains(search_term, na=False)
        
        # NDC search
        ndc_match = df.get('ndc_primary', pd.Series()).astype(str).str.contains(search_term, na=False)
        
        # Also check search keywords if available
        if 'search_keywords' in df.columns:
            keyword_match = df['search_keywords'].astype(str).str.lower().str.contains(search_term, na=False)
            mask = name_match | form_match | strength_match | keyword_match | enhanced_brand_match | brand_match | pharma_cleaned_match | pharma_match | ndc_match
        else:
            mask = name_match | form_match | strength_match | enhanced_brand_match | brand_match | pharma_cleaned_match | pharma_match | ndc_match
    
    # Use performance config for max results
    if max_results is None:
        max_results = PERFORMANCE_CONFIG['max_search_results']
    
    # Return top results efficiently
    results = df[mask].head(max_results)
    return results

@st.cache_data
def get_pharma_company_stats(df):
    """Get statistics about pharmaceutical companies in the dataset using cleaned names."""
    # Use cleaned pharmaceutical company names if available
    pharma_col = 'pharma_company_cleaned' if 'pharma_company_cleaned' in df.columns else 'major_pharma_primary'
    
    if pharma_col not in df.columns:
        return {}
    
    # Count medications by cleaned pharmaceutical companies
    pharma_counts = df[pharma_col].value_counts().head(20)
    
    # Extract company names from cleaned data (much simpler now!)
    company_names = set()
    for company in df[pharma_col].dropna().unique():
        if company and len(str(company).strip()) > 1:
            company_names.add(str(company).strip())
    
    return {
        'company_counts': pharma_counts.to_dict(),
        'company_names': sorted(list(company_names)),
        'total_with_pharma': len(df[df[pharma_col].notna()]),
        'total_medications': len(df),
        'using_cleaned_names': pharma_col == 'pharma_company_cleaned'
    }

@st.cache_data
def get_summary_stats(df):
    """Cache expensive summary statistics."""
    return {
        'total_medications': len(df),
        'complete_records': len(df[df['filled_columns'] == 5]),
        'avg_completeness': df['completeness_percent'].mean(),
        'avg_sigs': df['sig_count'].mean(),
        'unique_dose_forms': df['display_dose_form'].nunique(),
        'term_type_counts': df['term_type'].value_counts().to_dict()
    }

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
    """Main dashboard with overview statistics including NDC and pharmaceutical company data."""
    st.header("💊 Enhanced Medication Database Overview")
    
    # Main metrics with enhanced data
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Medications", f"{len(filtered_df):,}")
    with col2:
        dose_form_col = 'display_dose_form' if 'dose_form_clean' in filtered_df.columns else 'dose_form'
        st.metric("Dose Forms", f"{filtered_df[dose_form_col].nunique():,}")
    with col3:
        avg_sigs = filtered_df['sig_count'].mean()
        st.metric("Avg SIGs per Med", f"{avg_sigs:.1f}")
    with col4:
        ndc_count = filtered_df.get('has_ndc', pd.Series(False)).sum()
        st.metric("With NDC Codes", f"{ndc_count:,}")
    with col5:
        pharma_count = filtered_df.get('has_pharma_company', pd.Series(False)).sum()
        st.metric("Major Pharma", f"{pharma_count:,}")
    
    # Enhanced data availability metrics
    st.subheader("📊 Enhanced Data Coverage")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_sigs = filtered_df['sig_count'].sum()
        st.metric("Total SIG Instructions", f"{total_sigs:,}")
    with col2:
        if 'ndc_count' in filtered_df.columns:
            total_ndcs = filtered_df['ndc_count'].sum()
            st.metric("Total NDC Codes", f"{total_ndcs:,}")
        else:
            st.metric("Total NDC Codes", "0")
    with col3:
        if 'major_pharma_primary' in filtered_df.columns:
            unique_pharma = filtered_df['major_pharma_primary'].nunique()
            st.metric("Pharma Companies", f"{unique_pharma:,}")
        else:
            st.metric("Pharma Companies", "0")
    with col4:
        avg_completeness = filtered_df['completeness_percent'].mean()
        st.metric("Avg Data Completeness", f"{avg_completeness:.1f}%")
    
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
    
    # Pharmaceutical Company Analysis (use cleaned names if available)
    pharma_col = 'pharma_company_cleaned' if 'pharma_company_cleaned' in filtered_df.columns else 'major_pharma_primary'
    if pharma_col in filtered_df.columns:
        st.subheader("🏢 Top Pharmaceutical Companies (Cleaned Names)")
        col1, col2 = st.columns(2)
        
        with col1:
            pharma_counts = filtered_df[pharma_col].value_counts().head(10)
            if not pharma_counts.empty:
                fig_pharma = px.bar(
                    x=pharma_counts.values,
                    y=pharma_counts.index,
                    orientation='h',
                    title="Top 10 Pharmaceutical Companies (Standardized Names)"
                )
                fig_pharma.update_layout(yaxis={'categoryorder': 'total ascending'})
                st.plotly_chart(fig_pharma, use_container_width=True)
            else:
                st.info("No pharmaceutical company data available in current filter")
        
        with col2:
            # Data availability pie chart
            has_ndc = filtered_df.get('has_ndc', pd.Series(False)).sum()
            has_pharma = filtered_df.get('has_pharma_company', pd.Series(False)).sum()
            has_both = ((filtered_df.get('has_ndc', pd.Series(False))) & 
                       (filtered_df.get('has_pharma_company', pd.Series(False)))).sum()
            has_neither = len(filtered_df) - has_ndc - has_pharma + has_both
            
            fig_data = px.pie(
                values=[has_both, has_ndc-has_both, has_pharma-has_both, has_neither],
                names=['NDC + Pharma', 'NDC Only', 'Pharma Only', 'Neither'],
                title="Enhanced Data Availability"
            )
            st.plotly_chart(fig_data, use_container_width=True)
    
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
        # Enhanced completeness distribution
        completeness_counts = filtered_df['completeness_category'].value_counts()
        fig4 = px.pie(
            values=completeness_counts.values,
            names=completeness_counts.index,
            title="Data Completeness Distribution"
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
            # Create a clean display name
            display_parts = [row['display_drug_name']]
            if pd.notna(row['display_dose_form']):
                display_parts.append(f"({row['display_dose_form']})")
            display_name = " ".join(display_parts)
            
            with st.expander(f"💊 {display_name}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**RXCUI:** {row['rxcui']}")
                    if pd.notna(row['display_dose_form']) and str(row['display_dose_form']) != 'nan':
                        st.write(f"**Dose Form:** {row['display_dose_form']}")
                    if pd.notna(row['display_strength']) and str(row['display_strength']) != 'nan':
                        st.write(f"**Strength:** {row['display_strength']}")
                    # Data completeness and search keywords hidden for customer-facing interface
                
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

def medication_search_tab(df):
    """Enhanced medication search tab with brand name, NDC, and comprehensive filtering."""
    st.header("🔎 Enhanced Medication Search v3.0")
    st.markdown("Search by drug name, brand/company name, **HIPAA-standardized NDC code**, or any combination. All NDC codes now in 11-digit 5-4-2 format for billing compliance!")
    
    # Enhanced search interface
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_input = st.text_input(
            "🔍 Search medications:", 
            placeholder="Type drug name, company (e.g., 'Lilly', 'Pfizer'), NDC (e.g., '12345-6789-01'), dose form, or strength...",
            help="Enhanced search across all fields including pharmaceutical companies and HIPAA-standardized NDC codes (11-digit 5-4-2 format)"
        )
    
    with col2:
        search_mode = st.selectbox(
            "Search in:", 
            ["All fields", "Drug name only", "Brand/Company only", "NDC codes only", "Dose form only"],
            help="Choose specific search scope for more targeted results"
        )
    
    # Map search mode to internal values
    mode_mapping = {
        "All fields": "all",
        "Drug name only": "drug_name", 
        "Brand/Company only": "brand_name",
        "NDC codes only": "ndc",
        "Dose form only": "dose_form"
    }
    internal_mode = mode_mapping[search_mode]
    
    # Use optimized search function
    if search_input:
        # Use cached search function for better performance
        display_results = get_search_results(df, search_input, internal_mode, max_results=50)
        
        # Show results count and search mode info
        st.write(f"📊 **{len(display_results):,} medications found** in '{search_mode}' (showing top 50)")
        
        # Create expandable cards for each medication
        for idx, row in display_results.iterrows():
            # Create a summary line for the card with enhanced info
            summary_parts = [row['display_drug_name']]
            if pd.notna(row['display_dose_form']):
                summary_parts.append(f"({row['display_dose_form']})")
            if pd.notna(row['display_strength']):
                summary_parts.append(f"- {row['display_strength']}")
            
            # Add pharmaceutical company if available (use cleaned name first)
            pharma_company = row.get('pharma_company_cleaned') if pd.notna(row.get('pharma_company_cleaned')) else row.get('major_pharma_primary')
            if pd.notna(pharma_company):
                summary_parts.append(f"[{pharma_company}]")
            
            summary_line = " ".join(summary_parts)
            
            with st.expander(f"💊 {summary_line}"):
                # Create three columns for enhanced medication details
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    st.markdown("### 📋 Medication Details")
                    st.write(f"**RXCUI:** {row['rxcui']}")
                    st.write(f"**Name:** {row['display_drug_name']}")
                    st.write(f"**Term Type:** {row['term_type']}")
                    
                    if pd.notna(row['display_dose_form']):
                        st.write(f"**Dose Form:** {row['display_dose_form']}")
                    else:
                        st.write("**Dose Form:** _Not specified_")
                    
                    if pd.notna(row['display_strength']):
                        st.write(f"**Strength:** {row['display_strength']}")
                    else:
                        st.write("**Strength:** _Not specified_")
                
                with col2:
                    st.markdown("### 🏢 Company & Codes")
                    
                    # NDC Information (HIPAA Standardized)
                    if pd.notna(row.get('ndc_primary')):
                        st.write(f"**Primary NDC (HIPAA):** {row['ndc_primary']}")
                        st.caption("✅ 11-digit 5-4-2 format (billing ready)")
                        ndc_count = row.get('ndc_count', 0)
                        if ndc_count > 1:
                            st.write(f"**Total NDCs:** {ndc_count}")
                        
                        # Show original NDC if different
                        if pd.notna(row.get('ndc_primary_original')) and row.get('ndc_primary_original') != row.get('ndc_primary'):
                            st.write(f"**Original NDC:** {row['ndc_primary_original']}")
                    else:
                        st.write("**NDC:** _Not available_")
                    
                    # Pharmaceutical Company Information (use cleaned name first)
                    pharma_company = row.get('pharma_company_cleaned') if pd.notna(row.get('pharma_company_cleaned')) else row.get('major_pharma_primary')
                    if pd.notna(pharma_company):
                        st.write(f"**Pharma Company (Cleaned):** {pharma_company}")
                        if pd.notna(row.get('major_pharma_primary')) and row.get('pharma_company_cleaned') != row.get('major_pharma_primary'):
                            st.write(f"**Original Name:** {row['major_pharma_primary']}")
                    elif pd.notna(row.get('labeler_primary')):
                        st.write(f"**Labeler:** {row['labeler_primary']}")
                    else:
                        st.write("**Company:** _Not available_")
                    
                    # Show merged brand + drug name if available
                    if pd.notna(row.get('brand_drug_name_merged')):
                        st.write(f"**Merged Brand+Drug Name:** {row['brand_drug_name_merged']}")
                    
                    # Additional codes if available
                    if pd.notna(row.get('gpi_primary')):
                        st.write(f"**GPI Code:** {row['gpi_primary']}")
                
                with col3:
                    st.markdown("### 🧠 SIG Instructions")
                    
                    # Display primary SIG
                    if pd.notna(row['sig_primary']):
                        st.markdown("**Primary SIG:**")
                        st.info(row['sig_primary'])
                    
                    # Display all SIG instructions
                    if pd.notna(row['sig_instructions_json']):
                        try:
                            all_sigs = json.loads(row['sig_instructions_json'])
                            if all_sigs:
                                st.markdown(f"**All SIG Instructions ({len(all_sigs)}):**")
                                
                                for i, sig in enumerate(all_sigs, 1):
                                    # Highlight the primary SIG
                                    if sig == row['sig_primary']:
                                        st.markdown(f"**{i}. {sig}** ⭐ _(Primary)_")
                                    else:
                                        st.write(f"{i}. {sig}")
                            else:
                                st.warning("No SIG instructions available")
                        except:
                            st.error("Error parsing SIG instructions")
                    else:
                        st.warning("No SIG instructions available")
                
                # Enhanced download data
                st.markdown("---")
                medication_data = {
                    'rxcui': row['rxcui'],
                    'drug_name': row['display_drug_name'],
                    'term_type': row['term_type'],
                    'dose_form': row['display_dose_form'] if pd.notna(row['display_dose_form']) else '',
                    'strength': row['display_strength'] if pd.notna(row['display_strength']) else '',
                    'ndc_primary': row.get('ndc_primary', ''),
                    'ndc_count': row.get('ndc_count', 0),
                    'pharmaceutical_company_cleaned': row.get('pharma_company_cleaned', ''),
                    'pharmaceutical_company_original': row.get('major_pharma_primary', ''),
                    'labeler': row.get('labeler_primary', ''),
                    'merged_brand_drug_name': row.get('brand_drug_name_merged', ''),
                    'gpi_code': row.get('gpi_primary', ''),
                    'primary_sig': row['sig_primary'] if pd.notna(row['sig_primary']) else '',
                    'all_sigs': json.loads(row['sig_instructions_json']) if pd.notna(row['sig_instructions_json']) else []
                }
                
                medication_json = json.dumps(medication_data, indent=2)
                st.download_button(
                    label="📥 Download Enhanced Medication Data (JSON)",
                    data=medication_json,
                    file_name=f"medication_{row['rxcui']}_enhanced.json",
                    mime="application/json",
                    key=f"download_{row['rxcui']}"
                )
        
        if len(display_results) >= 50:
            st.info(f"💡 Showing top 50 results. Refine your search to see more specific matches.")
    
    else:
        # Show enhanced instructions when no search term
        st.markdown("""
        ### 🔍 Enhanced Search Capabilities
        
        **Start typing in the search box above to find medications:**
        
        - 🏷️ **By Drug Name:** Type medication name (e.g., "Aspirin", "Tylenol")
        - 🏢 **By Company:** Type pharmaceutical company (e.g., "Lilly", "Pfizer", "Johnson")
        - 🏷️ **By NDC Code:** Type NDC code (e.g., "0049-2410")
        - 💊 **By Dose Form:** Type form (e.g., "Tablet", "Capsule", "Solution") 
        - 💪 **By Strength:** Type strength (e.g., "500 MG", "10 ML")
        - 🔤 **Mixed Search:** Combine any terms
        
        **Enhanced Search Features:**
        - ✅ **Pharmaceutical Company Search** - Find all Lilly, Pfizer, etc. medications
        - ✅ **NDC Code Search** - Search by National Drug Code
        - ✅ **Real-time filtering** as you type
        - ✅ **Case-insensitive** search
        - ✅ **Multi-field** matching
        - ✅ **Targeted search modes** for specific fields
        
        **New Search Tips:**
        - Search "Lilly" to find all Eli Lilly medications
        - Search "Pfizer" to find all Pfizer medications  
        - Use NDC codes for precise identification
        - Combine company + drug name for specific results
        """)
        
        # Show pharmaceutical company examples
        pharma_stats = get_pharma_company_stats(df)
        if pharma_stats.get('company_names'):
            st.markdown("### 🏢 Available Pharmaceutical Companies:")
            company_cols = st.columns(3)
            for i, company in enumerate(pharma_stats['company_names'][:12]):  # Show top 12
                with company_cols[i % 3]:
                    if st.button(f"🔍 {company}", help=f"Search for {company} medications"):
                        st.experimental_set_query_params(search=company)
                        st.rerun()
        
        # Show some example searches
        st.markdown("### 🎯 Try These Example Searches:")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 Aspirin", help="Search for Aspirin medications"):
                st.rerun()
        
        with col2:
            if st.button("🔍 Lilly", help="Search for Eli Lilly medications"):
                st.rerun()
                
        with col3:
            if st.button("🔍 Tablet", help="Search for tablet medications"):
                st.rerun()
                
        with col4:
            if st.button("🔍 NDC", help="Search in NDC codes"):
                st.rerun()

def main():
    st.title("💊 Enhanced RxNorm Medication Database Explorer v3.0")
    st.markdown("Interactive dashboard for exploring 74,521+ medications with SIG instructions, **HIPAA-standardized NDC codes**, and pharmaceutical company data")
    
    # Performance status indicator
    with st.expander("⚡ Performance Status", expanded=False):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Search Limit", f"{PERFORMANCE_CONFIG['max_search_results']} results")
        with col2:
            st.metric("Table Limit", f"{PERFORMANCE_CONFIG['max_table_rows']} rows")
        with col3:
            st.metric("Caching", "✅ Enabled")
        with col4:
            st.metric("Enhanced Data", "✅ v3.0 HIPAA NDC")
    
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
    
    # Enhanced filters for new data
    st.sidebar.header("🏢 Enhanced Filters")
    
    # Pharmaceutical company filter (use cleaned names if available)
    pharma_col = 'pharma_company_cleaned' if 'pharma_company_cleaned' in df.columns else 'major_pharma_primary'
    if pharma_col in df.columns:
        pharma_companies = df[pharma_col].dropna().unique()
        if len(pharma_companies) > 0:
            # If using cleaned names, they're already standardized!
            if pharma_col == 'pharma_company_cleaned':
                company_display_names = set(pharma_companies)
            else:
                # Extract company names for cleaner display (legacy fallback)
                company_display_names = set()
                for company in pharma_companies:
                    if 'Lilly' in company:
                        company_display_names.add('Eli Lilly')
                    elif 'Pfizer' in company:
                        company_display_names.add('Pfizer')
                    elif 'Johnson' in company:
                        company_display_names.add('Johnson & Johnson')
                    elif 'Merck' in company:
                        company_display_names.add('Merck')
                    elif 'Novartis' in company:
                        company_display_names.add('Novartis')
                    elif 'Roche' in company:
                        company_display_names.add('Roche')
                    elif 'Bristol' in company:
                        company_display_names.add('Bristol-Myers Squibb')
                    else:
                        # Take first part of company name
                        first_part = company.split(',')[0].split(' ')[0]
                        if len(first_part) > 3:
                            company_display_names.add(first_part)
            
            pharma_options = ['All'] + sorted(list(company_display_names))
            selected_pharma = st.sidebar.selectbox("Pharmaceutical Company (Cleaned)", pharma_options)
        else:
            selected_pharma = 'All'
    else:
        selected_pharma = 'All'
    
    # Data availability filters
    show_with_ndc = st.sidebar.checkbox("Show only medications with NDC codes", 
                                       help="Filter to medications that have NDC codes available")
    show_with_pharma = st.sidebar.checkbox("Show only medications with pharmaceutical company data",
                                          help="Filter to medications with major pharmaceutical company information")
    
    # Apply basic filters
    filtered_df = df.copy()
    if selected_term_type != 'All':
        filtered_df = filtered_df[filtered_df['term_type'] == selected_term_type]
    if selected_dose_form != 'All':
        filtered_df = filtered_df[filtered_df[dose_form_col] == selected_dose_form]
    
    # Apply enhanced filters
    if selected_pharma != 'All' and pharma_col in filtered_df.columns:
        # Filter by pharmaceutical company (using cleaned names if available)
        filtered_df = filtered_df[
            filtered_df[pharma_col].str.contains(selected_pharma, case=False, na=False)
        ]
    
    if show_with_ndc and 'has_ndc' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['has_ndc']]
    
    if show_with_pharma and 'has_pharma_company' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['has_pharma_company']]
    
    # Create tabs - Added Medication Search tab
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview", 
        "🔍 Data Completeness", 
        "🎯 Quality Filters", 
        "🔎 Search & Details",
        "🔍 Medication Search"
    ])
    
    with tab1:
        main_dashboard_tab(df, filtered_df)
    
    with tab2:
        data_completeness_tab(df, filtered_df)
    
    with tab3:
        quality_filtered_df = quality_filters_tab(df)
    
    with tab4:
        search_tab(filtered_df)
    
    with tab5:
        medication_search_tab(filtered_df)
    
    # Enhanced download section in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Enhanced Download Options v3.0")
    
    # Download entire enhanced dataset
    st.sidebar.markdown("**📂 Complete Enhanced Dataset**")
    
    # Prepare full dataset for download
    full_csv = df.to_csv(index=False)
    st.sidebar.download_button(
        label="📥 Download Complete Enhanced Dataset",
        data=full_csv,
        file_name="rxnorm_enhanced_medication_database.csv",
        mime="text/csv",
        help=f"Download all {len(df):,} medications with SIG instructions, HIPAA-standardized NDC codes (11-digit), and pharmaceutical company data"
    )
    
    # Download current filtered view
    st.sidebar.markdown("**🔍 Current Filtered View**")
    csv = filtered_df.to_csv(index=False)
    filter_suffix = f"{selected_term_type}_{selected_dose_form}_{selected_pharma}".replace(" ", "_").replace("/", "_")
    st.sidebar.download_button(
        label="📥 Download Filtered Data",
        data=csv,
        file_name=f"filtered_enhanced_medications_{filter_suffix}.csv",
        mime="text/csv",
        help=f"Download current view ({len(filtered_df):,} medications)"
    )
    
    # Export pharmaceutical company data
    if 'major_pharma_primary' in filtered_df.columns and len(filtered_df[filtered_df['major_pharma_primary'].notna()]) > 0:
        st.sidebar.markdown("**🏢 Pharmaceutical Company Data**")
        pharma_export = []
        for idx, row in filtered_df[filtered_df['major_pharma_primary'].notna()].iterrows():
            pharma_export.append({
                'rxcui': row['rxcui'],
                'drug_name': row['display_drug_name'],
                'pharmaceutical_company': row['major_pharma_primary'],
                'labeler': row.get('labeler_primary', ''),
                'ndc_primary': row.get('ndc_primary', ''),
                'ndc_count': row.get('ndc_count', 0),
                'term_type': row['term_type'],
                'dose_form': row['display_dose_form'] if pd.notna(row['display_dose_form']) else '',
                'strength': row['display_strength'] if pd.notna(row['display_strength']) else ''
            })
        
        if pharma_export:
            pharma_df = pd.DataFrame(pharma_export)
            pharma_csv = pharma_df.to_csv(index=False)
            st.sidebar.download_button(
                label="📊 Download Pharma Company Data",
                data=pharma_csv,
                file_name="pharmaceutical_company_medications.csv",
                mime="text/csv",
                help=f"Download {len(pharma_export):,} medications with pharmaceutical company data"
            )
    
    # Export NDC data
    if 'ndc_primary' in filtered_df.columns and len(filtered_df[filtered_df['ndc_primary'].notna()]) > 0:
        st.sidebar.markdown("**🏷️ NDC Code Data**")
        ndc_export = []
        for idx, row in filtered_df[filtered_df['ndc_primary'].notna()].iterrows():
            # Parse all NDC codes if available
            try:
                all_ndcs = json.loads(row.get('ndc_codes_json', '[]')) if pd.notna(row.get('ndc_codes_json')) else [row['ndc_primary']]
            except:
                all_ndcs = [row['ndc_primary']]
            
            for ndc in all_ndcs:
                ndc_export.append({
                    'rxcui': row['rxcui'],
                    'drug_name': row['display_drug_name'],
                    'ndc_code': ndc,
                    'pharmaceutical_company': row.get('major_pharma_primary', ''),
                    'term_type': row['term_type'],
                    'dose_form': row['display_dose_form'] if pd.notna(row['display_dose_form']) else '',
                    'strength': row['display_strength'] if pd.notna(row['display_strength']) else ''
                })
        
        if ndc_export:
            ndc_df = pd.DataFrame(ndc_export)
            ndc_csv = ndc_df.to_csv(index=False)
            st.sidebar.download_button(
                label="📋 Download All NDC Codes",
                data=ndc_csv,
                file_name="all_ndc_codes.csv",
                mime="text/csv",
                help=f"Download {len(ndc_export):,} NDC code records"
            )
    
    # Export SIG instructions
    if len(filtered_df) > 0:
        st.sidebar.markdown("**🧠 SIG Instructions**")
        sig_export = []
        for idx, row in filtered_df.iterrows():
            if row['sig_instructions_json']:
                try:
                    sigs = json.loads(row['sig_instructions_json'])
                    for sig in sigs:
                        sig_export.append({
                            'rxcui': row['rxcui'],
                            'drug_name': row['display_drug_name'],
                            'pharmaceutical_company': row.get('major_pharma_primary', ''),
                            'ndc_primary': row.get('ndc_primary', ''),
                            'term_type': row['term_type'],
                            'dose_form': row['display_dose_form'] if pd.notna(row['display_dose_form']) else '',
                            'strength': row['display_strength'] if pd.notna(row['display_strength']) else '',
                            'sig_instruction': sig
                        })
                except:
                    pass
        
        if sig_export:
            sig_df = pd.DataFrame(sig_export)
            sig_csv = sig_df.to_csv(index=False)
            st.sidebar.download_button(
                label="📋 Download All SIG Instructions",
                data=sig_csv,
                file_name="enhanced_sig_instructions.csv",
                mime="text/csv",
                help=f"Download {len(sig_export):,} SIG instructions with company data"
            )
    
    # Enhanced dataset information
    st.sidebar.markdown("---")
    st.sidebar.markdown("**📊 Enhanced Dataset Info v3.0**")
    st.sidebar.write(f"Total medications: {len(df):,}")
    st.sidebar.write(f"Complete records: {len(df[df['filled_columns'] >= 5]):,}")
    st.sidebar.write(f"Average SIGs per med: {df['sig_count'].mean():.1f}")
    
    # Enhanced data statistics
    if 'has_ndc' in df.columns:
        ndc_count = df['has_ndc'].sum()
        st.sidebar.write(f"With HIPAA NDC codes: {ndc_count:,} ({(ndc_count/len(df)*100):.1f}%)")
    
    if 'has_pharma_company' in df.columns:
        pharma_count = df['has_pharma_company'].sum()
        st.sidebar.write(f"With pharma companies: {pharma_count:,} ({(pharma_count/len(df)*100):.1f}%)")
    
    if pharma_col in df.columns:
        unique_pharma = df[pharma_col].nunique()
        status = "(cleaned)" if pharma_col == 'pharma_company_cleaned' else "(original)"
        st.sidebar.write(f"Unique pharma companies: {unique_pharma:,} {status}")
    
    # v3.0 specific features
    st.sidebar.markdown("**🏥 v3.0 NDC Features:**")
    st.sidebar.write("✅ HIPAA 11-digit format (5-4-2)")
    st.sidebar.write("✅ Billing system compliant")
    st.sidebar.write("✅ CMS/Medicaid ready")
    
    # Performance tips
    create_performance_warning()
    
    # GitHub link
    st.sidebar.markdown("---")
    st.sidebar.markdown("**🔗 Resources**")
    st.sidebar.markdown("[📁 GitHub Repository](https://github.com/vineetdaniels2108/RxNormSIGProject)")
    st.sidebar.markdown("[📖 Usage Documentation](https://github.com/vineetdaniels2108/RxNormSIGProject/blob/main/DATA_USAGE_README.md)")
    st.sidebar.markdown("[🏢 Brand Name Search Index](data/brand_name_index.json)")

if __name__ == "__main__":
    main() 