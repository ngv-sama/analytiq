import streamlit as st
from data_utils import *
from data_analysis import *

from models import get_db, Dataset  # Import the Dataset model and database session
from sqlalchemy.orm import Session

# Try to import Plotly and install if not available
try:
    import plotly.express as px
except ModuleNotFoundError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "plotly"])
    import plotly.express as px

# Set page config for dark mode
st.set_page_config(
    page_title="AnalytiQ",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Function to display the summary as tiles
def display_summary_tiles(summary):
    """Displays the summary statistics in a tile format."""
    col1, col2, col3 = st.columns(3)
    col1.metric("Number of Rows", summary['Number of Rows'])
    col1.metric("Number of Columns", summary['Number of Columns'])
    col2.metric("Missing Values", summary['Missing Values'])
    col2.metric("Duplicate Rows", summary['Duplicate Rows'])
    col3.metric("Memory Usage (MB)", summary['Memory Usage (MB)'])

# Function to display the column-level summary and distribution side by side
def display_column_summary(df, column):
    """Displays the summary of the selected column with distribution plots."""
    summary = column_summary(df, column)
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("Data Type:", summary['Data Type'])
        st.write("Unique Values:", summary['Unique Values'])
        st.write("Missing Values:", summary['Missing Values'])
        st.write("Mean:", summary['Mean'])
        st.write("Median:", summary['Median'])
        st.write("Mode:", summary['Mode'])
        st.write("Standard Deviation:", summary['Standard Deviation'])
        st.write("Min:", summary['Min'])
        st.write("Max:", summary['Max'])
    
    with col2:
        st.subheader(f"Distribution of {column}")
        if pd.api.types.is_numeric_dtype(df[column]):
            fig = px.histogram(df, x=column, marginal="box", nbins=30, title=f'Distribution of {column}')
        else:
            fig = px.histogram(df, x=column, color=column, title=f'Distribution of {column}')
        st.plotly_chart(fig, use_container_width=True)

# Function to handle the first tab (Data Summary)
def handle_data_summary_tab(filtered_data):
    """Handles all content and logic within the Data Summary tab."""
    st.header("Data Summary")
    
    # Display summary statistics in tiles
    summary = generate_summary(filtered_data)
    display_summary_tiles(summary)
    
    # Combined accordion with two tabs for detailed statistics and column-level summary
    st.header("Detailed Analysis")
    with st.expander("View Detailed Analysis", expanded=False):
        sub_tabs = st.tabs(["Detailed Statistics", "Column-Level Summary"])
        
        with sub_tabs[0]:
            st.subheader("Detailed Statistics")
            st.dataframe(detailed_statistics(filtered_data), use_container_width=True)
        
        with sub_tabs[1]:
            st.subheader("Column-Level Summary")
            selected_column = st.selectbox("Select Column", filtered_data.columns)
            if selected_column:
                display_column_summary(filtered_data, selected_column)

def handle_data_analysis_tab(filtered_data):
    """Handles all content and logic within the Data Analysis Tab."""
    st.header("Data Analysis")
    st.write("This tab will host various analysis tools, such as univariate, bivariate, and multivariate analysis, along with other advanced data analysis features.")
    
    # Dropdown for analysis options
    analysis_option = st.selectbox(
        "Select an Analysis Type",
        options=[
            "Univariate Analysis",
            "Bivariate Analysis",
            "Multivariate Analysis",
            "Correlation Analysis",
            "Cross Tabulation"
        ]
    )
    
    # Show the description based on the selected analysis
    description = {
        "Univariate Analysis": "Analyze the distribution and summary statistics of individual variables.",
        "Bivariate Analysis": "Analyze the relationship between two variables.",
        "Multivariate Analysis": "Analyze relationships involving more than two variables.",
        "Correlation Analysis": "Analyze correlations between numerical variables.",
        "Cross Tabulation": "Analyze relationships between categorical variables."
    }[analysis_option]
    
    st.subheader(analysis_option)
    st.write(f"Description: {description}")
    st.markdown("---")
    
    # Univariate Analysis implementation
    if analysis_option == "Univariate Analysis":
        selected_column = st.selectbox("Select Column for Univariate Analysis", filtered_data.columns)
        if selected_column:
            display_univariate_analysis(filtered_data, selected_column)
    
    # Bivariate Analysis implementation
    elif analysis_option == "Bivariate Analysis":
        col1, col2 = st.columns(2)
        with col1:
            x_column = st.selectbox("Select X-axis Column", filtered_data.columns)
        with col2:
            y_column = st.selectbox("Select Y-axis Column", filtered_data.columns)
        if x_column and y_column:
            display_bivariate_analysis(filtered_data, x_column, y_column)
    # Multivariate Analysis implementation
    elif analysis_option == "Multivariate Analysis":
        selected_columns = st.multiselect("Select Columns for Multivariate Analysis", filtered_data.columns)
        if selected_columns:
            display_multivariate_analysis(filtered_data, selected_columns)
    elif analysis_option == "Correlation Analysis":
        display_correlation_analysis(filtered_data)

def main():
    st.title("AnalytiQ")

    # Fetch datasets from the database
    db: Session = next(get_db())
    datasets = db.query(Dataset).all()
    
    if not datasets:
        st.write("No datasets available. Please upload a dataset first.")
        return

    dataset_names = [dataset.name for dataset in datasets]

    # Sidebar for dataset selection, limit input, and filters
    st.sidebar.header("Select Dataset and Filters")
    dataset_name = st.sidebar.selectbox("Select Dataset", dataset_names)
    data_limit = st.sidebar.number_input("Number of Rows to Fetch", min_value=1, value=1000, step=1000)

    # Load the selected dataset with a loading spinner
    if dataset_name:
        selected_dataset = db.query(Dataset).filter(Dataset.name == dataset_name).first()
        data_path = selected_dataset.filepath
        
        with st.spinner(f"Loading {dataset_name}..."):
            selected_data = load_data(data_path, data_limit)
        
        # Sidebar filters
        st.sidebar.subheader("Filter Data")
        filters = {}
        for column in selected_data.columns:
            unique_vals = selected_data[column].unique()
            if len(unique_vals) < 100:  # Only show filter options if there are less than 100 unique values
                filters[column] = st.sidebar.selectbox(f"Filter by {column}", options=[None] + list(unique_vals))
        
        # Apply filters
        filtered_data = apply_filters(selected_data, filters)
        
        # Tabs for different views (e.g., Data View, Analysis, etc.)
        tabs = st.tabs(["Summary", "Analysis", "Other Tab 2"])
        
        with tabs[0]:
            handle_data_summary_tab(filtered_data)
        
        with tabs[1]:
            handle_data_analysis_tab(filtered_data)
        
        with tabs[2]:
            st.header("Other Analysis 2")
            st.write("Content for the third tab goes here.")
        
        # View Data section that remains constant across all tabs
        st.sidebar.header("View Data")
        st.write(f"Displaying first {data_limit} rows of {dataset_name}")
        st.dataframe(filtered_data, use_container_width=True)

if __name__ == "__main__":
    main()