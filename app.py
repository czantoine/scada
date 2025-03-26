import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

# Function to compare values and calculate error margins for one file
def compare_values_one_file(row, col1, col2):
    if pd.isnull(row[col1]) or pd.isnull(row[col2]):
        return {'Column1': col1, 'Column2': col2, 'Value1': row[col1], 'Value2': row[col2], 'Difference': 'Missing value', 'Percentage': 'N/A'}
    else:
        difference = row[col1] - row[col2]
        percentage = (difference / row[col1]) * 100 if row[col1] != 0 else 'N/A'
        return {'Column1': col1, 'Column2': col2, 'Value1': row[col1], 'Value2': row[col2], 'Difference': difference, 'Percentage': f'{percentage:.2f}%'}

# Function to apply color based on percentage deviation
def apply_color(val):
    if isinstance(val, str) and '%' in val:
        percentage = float(val.replace('%', ''))
        if percentage == 'N/A':
            return ''
        elif percentage <= 2 and percentage >= -2:
            color = 'rgba(0, 255, 0, 0.3)'  # light green background
        elif percentage <= 5 and percentage >= -5:
            color = 'rgba(255, 165, 0, 0.3)'  # light orange background
        else:
            color = 'rgba(255, 0, 0, 0.3)'  # light red background

        return f'background-color: {color}'
    return ''

# Streamlit interface
st.title('Data SCADA Validation')

# File uploader in the sidebar
file = st.sidebar.file_uploader('Upload the Excel file', type='xlsx')

if file:
    df = pd.read_excel(file, engine='openpyxl')

    # Check if the DataFrame has content
    if df.empty:
        st.warning('The uploaded file is empty. Please upload a valid file with data.')
    else:
        st.write(f'Data loaded: {df.shape[0]} rows and {df.shape[1]} columns.')

        selected_columns = st.multiselect('Select columns to compare', df.columns)

        if len(selected_columns) == 2:
            col1, col2 = selected_columns
            with st.spinner('Calculating...'):
                results = []
                total_percentage = 0
                green_count = 0
                orange_count = 0
                red_count = 0
                sum_value1 = 0
                sum_value2 = 0
                sum_valueA = 0
                valid_count = 0
                
                for i in range(len(df)):
                    row = df.iloc[i]
                    errors = compare_values_one_file(row, col1, col2)
                    results.append(errors)
                    
                    # Processing percentage for color categorization
                    if isinstance(errors['Percentage'], str) and '%' in errors['Percentage']:
                        percentage = float(errors['Percentage'].replace('%', ''))
                        if percentage != 'N/A':
                            total_percentage += percentage
                            valid_count += 1
                        if percentage <= 2 and percentage >= -2:
                            green_count += 1
                        elif percentage <= 5 and percentage >= -5:
                            orange_count += 1
                        else:
                            red_count += 1
                    
                    # Sum up values for SCADA result deviation
                    if errors['Value1'] != 'Missing value' and errors['Value2'] != 'Missing value':
                        sum_value1 += row[col1]
                        sum_value2 += row[col2]
                        sum_valueA += row[col1]  # assuming sum_valueA is meant to track the first column for SCADA deviation

                results_df = pd.DataFrame(results)
                
                # Apply color formatting only to Percentage column
                styled_df = results_df.style.applymap(apply_color, subset=['Percentage'])
                
                st.write('Comparison Results:')
                st.dataframe(styled_df.set_table_styles([{'selector': 'th', 'props': [('font-size', '20px')]}]), width=1200)  # Increase the width for larger display
                
                # Calculate average percentage deviation
                if valid_count > 0:
                    total_percentage_abs = total_percentage  # Ne pas oublier de garder la valeur absolue
                    total_percentage_abs = sum(abs(float(errors['Percentage'].replace('%', ''))) for errors in results if isinstance(errors['Percentage'], str) and '%' in errors['Percentage'])
                    average_percentage_deviation = total_percentage_abs / valid_count
                    st.write(f'**Average Percentage Deviation** (absolute): {average_percentage_deviation:.2f}%')
                else:
                    st.write('**Average Percentage Deviation**: N/A')
                
                # Calculate SCADA result deviation
                if sum_valueA != 0:
                    custom_calculation = (sum_value1 + sum_value2) / sum_valueA
                    st.write(f'**SCADA Result Deviation**: {custom_calculation:.2f}')
                else:
                    st.write('**SCADA Result Deviation**: N/A')
                
                # Create a pie chart to visualize the percentage of green, orange, and red data
                pie_data = {'Color': ['Green (-2% to +2%)', 
                                      'Orange (-5% to +5%)', 
                                      'Red (> 5% or < -5%)'],
                            'Count': [green_count, orange_count, red_count]}

                # Define corresponding colors for the pie chart
                pie_colors = ['rgba(0, 255, 0, 0.3)',  # light green for Green
                              'rgba(255, 165, 0, 0.3)',  # light orange for Orange
                              'rgba(255, 0, 0, 0.3)']    # light red for Red

                pie_df = pd.DataFrame(pie_data)

                # If there's data for the pie chart, display it
                if pie_df['Count'].sum() > 0:
                    fig = px.pie(pie_df, names='Color', values='Count', title='Distribution of Data by Percentage Deviation',
                                 color='Color', color_discrete_map=dict(zip(pie_df['Color'], pie_colors)),
                                 hole=0.3)  # Optional, to make it a donut chart for better text positioning

                    # Adjust textinfo to show the percentage outside the chart
                    fig.update_traces(textinfo='percent', textposition='outside', pull=[0.1, 0.1, 0.1])

                    st.plotly_chart(fig)
                    
                    # Add the legend with descriptions below the pie chart
                    st.markdown("""
                    ### Legend for Percentage Deviation:
                    - **Green**: Percentage deviations between **-2% and +2%**, indicating a very small deviation from the expected values.
                    - **Orange**: Percentage deviations between **-5% and +5%**, representing a moderate but acceptable deviation.
                    - **Red**: Percentage deviations greater than **5% or less than -5%**, suggesting significant discrepancies that require attention.
                    """)
                else:
                    st.warning('No data to display in the pie chart.')

else:
    st.info('Please upload an Excel file to get started.')
