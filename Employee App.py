import streamlit as st 
import pandas as pd
import numpy as np
import altair as alt
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import load_model
from vega_datasets import data
from scipy.interpolate import make_interp_spline
import matplotlib.pyplot as plt

def load_data():
    employee_df = pd.read_csv(r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\Employee_Behaviour.csv")
    return employee_df

def load_autoencoder_model():
    autoencoder = load_model(r"C:\Users\Nitya\Downloads\ThalesGentech\ThalesGentech\autoencoder_model.keras")
    return autoencoder

def validate_employee_behavior(employee_id, employee_df, autoencoder):
    """
    Function to validate an employee's behavior based on reconstructed error 
    from an autoencoder model.

    Behavior_Label categories:
    - Suspicious:
        * Idle_Time: Higher than average but not excessive.
        * File_Access_Frequency: Unusual frequency (either too high or too low).
        * VPN_Usage: Inconsistent or from unusual locations.
        * Work_Duration: Shorter than expected work hours.

    - Critical:
        * Idle_Time: Very high, suggesting disengagement or neglect.
        * File_Access_Frequency: Extremely high (potential data exfiltration) or zero (no productivity).
        * VPN_Usage: Consistent use from suspicious/unauthorized locations.
        * Work_Duration: Extremely short or excessively long hours without justification.
        * Latitude/Longitude: Geolocation inconsistent with approved areas or sudden location changes.
    """
    features = ['Work_Duration', 'Idle_Time', 'File_Access_Frequency', 'VPN_Usage', 'Latitude', 'Longitude']
    X = employee_df[features]

    # Scale features
    scaler = MinMaxScaler()
    X_scaled = scaler.fit_transform(X)

    # Filter data for specific employee
    employee_data = employee_df[employee_df['Employee_ID'] == employee_id]

    # Handle case where employee data is not found
    if employee_data.empty:
        return None

    # Scale features for the selected employee
    employee_features = employee_data[features]
    employee_scaled = scaler.transform(employee_features)

    # Predict and calculate reconstruction error
    reconstructed_employee = autoencoder.predict(employee_scaled)
    mse = np.mean(np.power(employee_scaled - reconstructed_employee, 2), axis=1)
    
    # Calculate anomaly threshold
    threshold = np.percentile(mse, 95)
    anomaly_flag = mse > threshold

    # Extract behavior label
    behavior_label = employee_data['Behavior_Label'].iloc[0]

    # Build result dictionary
    result = {
        'Employee_ID': employee_id,
        'Department': employee_data['Department'].iloc[0],
        'Role': employee_data['Role'].iloc[0],
        'Behavior_Label': behavior_label,
        'Work_Duration': employee_data['Work_Duration'].iloc[0],
        'Idle_Time': employee_data['Idle_Time'].iloc[0],
        'File_Access_Frequency': employee_data['File_Access_Frequency'].iloc[0],
        'VPN_Usage': employee_data['VPN_Usage'].iloc[0],
        'Reconstruction_Error': mse[0],
        'Is_Anomaly': bool(anomaly_flag[0]),
        'Login_Timestamp': employee_data['Login_Timestamp'].iloc[0],
        'Logout_Timestamp': employee_data['Logout_Timestamp'].iloc[0],
        'Latitude': employee_data['Latitude'].iloc[0],
        'Longitude': employee_data['Longitude'].iloc[0]
    }

    return result


def create_peak_hours_chart(employee_data):
    """
    Create an enhanced peak hours activity chart with new theme colors and better aesthetics
    """
    # Data preparation
    employee_data['Login_Timestamp'] = pd.to_datetime(employee_data['Login_Timestamp'])
    employee_data['Logout_Timestamp'] = pd.to_datetime(employee_data['Logout_Timestamp'])
    login_hour = employee_data['Login_Timestamp'].dt.hour.iloc[0]
    logout_hour = employee_data['Logout_Timestamp'].dt.hour.iloc[0]

    # Calculate activity data
    hours_data = pd.DataFrame({
        'Hour': range(24),
        'Work_Activity': 0,
        'Period': ['Off Hours'] * 24,
        'Hour_Label': [(f'{i:02d}:00' if i < 12 else f'{i-12:02d}:00 PM' if i > 12 else '12:00 PM') for i in range(24)]
    })
    
    work_duration = employee_data['Work_Duration'].iloc[0]

    # Distribute work activity
    if login_hour <= logout_hour:
        hours_data.loc[login_hour:logout_hour, 'Work_Activity'] += work_duration / (logout_hour - login_hour + 1)
        hours_data.loc[login_hour:logout_hour, 'Period'] = 'Working Hours'
    else:
        total_hours = 24 - login_hour + logout_hour + 1
        hours_data.loc[login_hour:23, 'Work_Activity'] += work_duration / total_hours
        hours_data.loc[0:logout_hour, 'Work_Activity'] += work_duration / total_hours
        hours_data.loc[login_hour:23, 'Period'] = 'Working Hours'
        hours_data.loc[0:logout_hour, 'Period'] = 'Working Hours'

    # Create enhanced chart
    base = alt.Chart(hours_data).encode(
        x=alt.X('Hour:O',
                axis=alt.Axis(
                    title='Time of Day',
                    labelAngle=0,
                    titleFontSize=14,
                    labelFontSize=12,
                    titleFontWeight='bold',
                    grid=False,
                    domain=True,
                    domainColor='#191970',
                    tickColor='#191970'
                ),
                scale=alt.Scale(paddingInner=0.2)
        ),
        tooltip=[
            alt.Tooltip('Hour_Label:N', title='Time'),
            alt.Tooltip('Work_Activity:Q', title='Activity Level', format='.2f'),
            alt.Tooltip('Period:N', title='Period')
        ]
    )

    # Gradient background
    area = base.mark_area(
        opacity=0.2,
        color='#191970'
    ).encode(
        y=alt.Y('Work_Activity:Q',
                scale=alt.Scale(domain=[0, hours_data['Work_Activity'].max() * 1.2])),
        color=alt.Color('Period:N',
                       scale=alt.Scale(range=['#d2ebff', '#191970']),
                       legend=None)
    )

    # Main activity line
    line = base.mark_line(
        strokeWidth=3,
        color='#191970',
        point=True,
        interpolate='basis'
    ).encode(
        y=alt.Y('Work_Activity:Q',
                axis=alt.Axis(
                    title='Activity Level',
                    titleFontSize=14,
                    labelFontSize=12,
                    titleFontWeight='bold',
                    grid=True,
                    gridColor='#d2ebff',
                    gridWidth=0.5,
                    domain=True,
                    domainColor='#191970'
                ))
    )

    # Interactive points
    points = base.mark_circle(
        size=100,
        color='#191970',
        opacity=0.6,
        stroke='#ffffff',
        strokeWidth=2
    ).encode(
        y='Work_Activity:Q'
    ).add_selection(
        alt.selection_single(
            on='mouseover',
            nearest=True,
            empty='none',
            clear='mouseout'
        )
    )

    # Time markers
    login_mark = alt.Chart(pd.DataFrame({
        'Hour': [login_hour],
        'Label': ['Login Time'],
        'Hour_Label': [hours_data.iloc[login_hour]['Hour_Label']]
    })).mark_rule(
        color='#28a745',
        strokeDash=[4, 4],
        strokeWidth=2
    ).encode(
        x='Hour:O',
        tooltip=[
            alt.Tooltip('Label:N', title='Event'),
            alt.Tooltip('Hour_Label:N', title='Time')
        ]
    )

    logout_mark = alt.Chart(pd.DataFrame({
        'Hour': [logout_hour],
        'Label': ['Logout Time'],
        'Hour_Label': [hours_data.iloc[logout_hour]['Hour_Label']]
    })).mark_rule(
        color='#dc3545',
        strokeDash=[4, 4],
        strokeWidth=2
    ).encode(
        x='Hour:O',
        tooltip=[
            alt.Tooltip('Label:N', title='Event'),
            alt.Tooltip('Hour_Label:N', title='Time')
        ]
    )

    # Combine layers
    final_chart = (area + line + points + login_mark + logout_mark).properties(
        title={
            'text': 'Daily Activity Pattern',
            'subtitle': ['Activity distribution throughout the day',
                        'Green: Login time | Red: Logout time'],
            'fontSize': 20,
            'subtitleFontSize': 14,
            'anchor': 'start',
            'color': '#191970'
        },
        width=600,
        height=400
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        domainColor='#191970',
        tickColor='#191970',
        labelColor='#191970',
        titleColor='#191970'
    ).configure_title(
        color='#191970',
        subtitleColor='#666666'
    )

    return final_chart




def create_behavior_comparison_chart(employee_data, department_data, features):
    """
    Create a grouped bar chart comparing employee metrics directly with department averages
    """
    # Calculate department averages
    department_avg = department_data[features].mean()
    employee_values = employee_data[features].iloc[0]
    
    # Create comparison dataframe in the desired format
    comparison_data = []
    for feature in features:
        comparison_data.extend([
            {
                'Feature': feature,
                'Category': 'Employee',
                'Value': employee_values[feature]
            },
            {
                'Feature': feature,
                'Category': 'Department Average',
                'Value': department_avg[feature]
            }
        ])
    
    comparison_df = pd.DataFrame(comparison_data)
    
    # Create the grouped bar chart
    chart = alt.Chart(comparison_df).mark_bar(
        cornerRadiusTopLeft=5,
        cornerRadiusTopRight=5,
        width=25  # Adjust bar width
    ).encode(
        x=alt.X('Feature:N',
                title='Metrics',
                axis=alt.Axis(labelAngle=0, labelPadding=10)),
        y=alt.Y('Value:Q',
                title='Value',
                scale=alt.Scale(zero=False)),
        xOffset=alt.XOffset("Category:N"),  # This creates the grouping
        color=alt.Color('Category:N',
                       scale=alt.Scale(range=['#3498db', '#2ecc71']),
                       legend=alt.Legend(
                           title='',
                           orient='top',
                           labelFontSize=12
                       )),
        tooltip=[
            alt.Tooltip('Feature:N', title='Metric'),
            alt.Tooltip('Category:N', title='Type'),
            alt.Tooltip('Value:Q', title='Value', format='.2f')
        ]
    ).properties(
        title={
            'text':'',
            'fontSize': 35,
            'subtitleFontSize': 14,
            'anchor': 'start',
            'color': '#2c3e50'
        },
        width=800,
        height=400
    ).configure_view(
        stroke=None
    ).configure_axis(
        grid=True,
        gridColor='#edf2f7',
        gridWidth=1.0,
        labelColor='#2c3e50',
        titleColor='#2c3e50',
        labelFontSize=12,
        titleFontSize=14
    )
    
    return chart

def create_peak_hours_chart(employee_data):
    """
    Create a new enhanced line graph showing peak hours activity
    """
    # Convert timestamps to datetime
    employee_data['Login_Timestamp'] = pd.to_datetime(employee_data['Login_Timestamp'])
    employee_data['Logout_Timestamp'] = pd.to_datetime(employee_data['Logout_Timestamp'])

    # Extract login and logout hours
    login_hour = employee_data['Login_Timestamp'].dt.hour.iloc[0]
    logout_hour = employee_data['Logout_Timestamp'].dt.hour.iloc[0]

    # Calculate work activity for each hour
    hours_data = pd.DataFrame({
        'Hour': range(24),
        'Work_Activity': 0,
        'Period': 'Off Hours'
    })
    
    work_duration = employee_data['Work_Duration'].iloc[0]

    # Distribute work activity and mark working hours
    if login_hour <= logout_hour:
        active_hours = range(login_hour, logout_hour + 1)
        hours_data.loc[login_hour:logout_hour, 'Work_Activity'] += work_duration / (logout_hour - login_hour + 1)
        hours_data.loc[login_hour:logout_hour, 'Period'] = 'Working Hours'
    else:
        active_hours = list(range(login_hour, 24)) + list(range(0, logout_hour + 1))
        total_hours = 24 - login_hour + logout_hour + 1
        hours_data.loc[login_hour:23, 'Work_Activity'] += work_duration / total_hours
        hours_data.loc[0:logout_hour, 'Work_Activity'] += work_duration / total_hours
        hours_data.loc[login_hour:23, 'Period'] = 'Working Hours'
        hours_data.loc[0:logout_hour, 'Period'] = 'Working Hours'

    # Create the multi-layer chart
    
    # Base area layer for working hours highlighting
    area_highlight = alt.Chart(hours_data).mark_area(
        opacity=0.1,
        color='#34495e'
    ).encode(
        x='Hour:O',
        y=alt.Y('Work_Activity:Q',
                scale=alt.Scale(domain=[0, hours_data['Work_Activity'].max() * 1.2])),
        color=alt.Color('Period:N',
                       scale=alt.Scale(range=['#f8f9fa', '#e2e8f0']),
                       legend=None)
    )

    # Main line layer
    line = alt.Chart(hours_data).mark_line(
        strokeWidth=3,
        color='#3498db',
        interpolate='monotone'
    ).encode(
        x=alt.X('Hour:O',
                title='Hour of Day',
                axis=alt.Axis(
                    labelAngle=0,
                    grid=False,
                    tickMinStep=1
                )),
        y=alt.Y('Work_Activity:Q',
                title='Activity Level',
                axis=alt.Axis(grid=True, gridColor='#edf2f7', gridWidth=0.5))
    )

    # Interactive points layer
    points = alt.Chart(hours_data).mark_circle(
        size=100,
        opacity=0,
        color='#3498db'
    ).encode(
        x='Hour:O',
        y='Work_Activity:Q',
        tooltip=[
            alt.Tooltip('Hour:O', title='Hour'),
            alt.Tooltip('Work_Activity:Q', title='Activity Level', format='.2f'),
            alt.Tooltip('Period:N', title='Period')
        ]
    ).add_selection(
        alt.selection_single(
            on='mouseover',
            nearest=True,
            empty='none',
            clear='mouseout'
        )
    )

    # Login marker
    login_mark = alt.Chart(pd.DataFrame({'Hour': [login_hour], 'Label': ['Login']})).mark_rule(
        color='#27ae60',
        strokeDash=[4, 4],
        strokeWidth=2
    ).encode(
        x='Hour:O',
        tooltip=[alt.Tooltip('Label:N', title='Event')]
    )

    # Logout marker
    logout_mark = alt.Chart(pd.DataFrame({'Hour': [logout_hour], 'Label': ['Logout']})).mark_rule(
        color='#e74c3c',
        strokeDash=[4, 4],
        strokeWidth=2
    ).encode(
        x='Hour:O',
        tooltip=[alt.Tooltip('Label:N', title='Event')]
    )

    # Combine all layers
    final_chart = (area_highlight + line + points + login_mark + logout_mark).properties(
        title={
            'text': ' ',
            'subtitle': 'Showing work activity distribution with highlighted working hours',
            'fontSize': 20,
            'subtitleFontSize': 14,
            'anchor': 'start',
            'color': '#2c3e50'
        },
        width=900,
        height=400
    ).configure_view(
        strokeWidth=0
    ).interactive()

    return final_chart

def main():
    # Enhanced CSS with new color scheme
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

        body {
            background-color: #d2ebff;
            color: #191970;
            font-family: 'Poppins', sans-serif;
        }

        .stApp {
            background: linear-gradient(135deg, #d2ebff 0%, #ffffff 100%);
        }

        .main .block-container {
            padding: 2rem;
        }

        /* Sidebar Styling */
        .css-1d391kg {
            background-color: #191970;
        }

        .css-1d391kg .block-container {
            padding: 2rem 1rem;
        }

        .sidebar .sidebar-content {
            background-color: #191970;
        }

        /* Headers */
        h1, h2, h3 {
            color: #191970;
            font-weight: 600;
            letter-spacing: -0.5px;
        }

        /* KPI Cards */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin: 1.5rem 0;
        }

        .kpi-card {
            background: linear-gradient(135deg, #191970 0%, #1e215a 100%);
            border-radius: 15px;
            padding: 1.5rem;
            color: #d2ebff;
            box-shadow: 0 8px 16px rgba(25, 25, 112, 0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .kpi-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 20px rgba(25, 25, 112, 0.15);
        }

        .kpi-title {
            font-size: 0.9rem;
            font-weight: 500;
            opacity: 0.9;
            margin-bottom: 0.5rem;
        }

        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            margin: 0;
        }

        /* Employee Info Card */
        .employee-card {
            background: #ffffff;
            border-radius: 15px;
            padding: 2rem;
            box-shadow: 0 8px 16px rgba(25, 25, 112, 0.1);
            color: #191970;
            margin: 1.5rem 0;
        }

        .employee-header {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #d2ebff;
        }

        .employee-info {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 1rem;
        }

        .info-item {
            padding: 0.5rem 0;
        }

        .info-label {
            font-size: 0.9rem;
            font-weight: 500;
            opacity: 0.8;
        }

        .info-value {
            font-size: 1.1rem;
            font-weight: 600;
        }

        /* Status Boxes */
        .status-box {
            padding: 1rem;
            border-radius: 10px;
            font-weight: 600;
            text-align: center;
            margin: 1rem 0;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }

        .normal {
            background-color: #28a745;
            color: white;
        }

        .suspicious {
            background-color: #ffc107;
            color: #000;
        }

        .critical {
            background-color: #dc3545;
            color: white;
        }

        /* Charts Container */
        .chart-container {
            background: #ffffff;
            border-radius: 10px;
            padding: 1.0rem;
            margin: 0.5rem 0;
            box-shadow: 0 8px 16px rgba(25, 25, 112, 0.1);
        }

        .chart-title {
            color: #191970;
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 1rem;
        }

        /* Custom Streamlit Elements */
        .stSelectbox {
            color: #191970;
        }

        .stSelectbox > div > div {
            background-color: #ffffff;
            border-radius: 8px;
        }

        /* Graphs */
        .vega-embed {
            background: #ffffff;
            border-radius: 15px;
            padding: 0.4rem;
            box-shadow: 0 4px 8px rgba(25, 25, 112, 0.1);
        }
        </style>
        """, unsafe_allow_html=True)

    # Dashboard Header
    st.markdown("""
        <div style='text-align: center; padding: 1rem 0;'>
            <h1 style='color: #191970; font-size: 2.5rem; font-weight: 700;'>📊 Employee Behavior Intelligence</h1>
        </div>
    """, unsafe_allow_html=True)

    # Load data
    employee_df = load_data()
    autoencoder = load_autoencoder_model()

    # Sidebar with enhanced styling
    st.sidebar.markdown("""
        <div style='padding: 1rem 0;'>
            <h2 style='color: #191970; font-size: 1.5rem; font-weight: 600;'>🔍 Employee Analysis</h2>
        </div>
    """, unsafe_allow_html=True)
    
    departments = employee_df['Department'].unique()
    selected_department = st.sidebar.selectbox('Select Department', departments)
    department_employees = employee_df[employee_df['Department'] == selected_department]
    employee_ids = department_employees['Employee_ID'].unique()
    selected_id = st.sidebar.selectbox('Select Employee ID', employee_ids)
    
    if st.sidebar.button('Department Analysis'):
    # Display the department analysis heading with custom styling
        st.markdown("""
        <style>
        .department-header {
            background-color: #191970;
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 25px;
            text-align: center;
        }
        .kpi-card {
            background-color: #87CEFB;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
            margin: 10px;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        }
        .kpi-metric {
            font-size: 24px;
            font-weight: bold;
            color: #191970;
        }
        .kpi-label {
            font-size: 16px;
            color: #191970;
            margin-top: 5px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    st.markdown(f"<div class='department-header'><h2>📊 {selected_department} Department Analysis</h2></div>", unsafe_allow_html=True)
    
    # Filter data for the selected department
    department_data = employee_df[employee_df['Department'] == selected_department]
    
    # Calculate metrics
    total_employees = len(department_data)
    anomaly_count = department_data['Access_Anomaly_Flag'].sum()
    anomaly_rate = (anomaly_count / total_employees) * 100
    suspicious_count = len(department_data[department_data['Behavior_Label'] == 'Suspicious'])
    critical_count = len(department_data[department_data['Behavior_Label'] == 'Critical'])
    
    # Create three columns for KPI cards
    col1, col2, col3 = st.columns(3)
    
    # KPI Cards
    with col1:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-metric'>{total_employees}</div>
                <div class='kpi-label'>Total Employees</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-metric'>{suspicious_count}</div>
                <div class='kpi-label'>Suspicious Activities</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-metric'>{critical_count}</div>
                <div class='kpi-label'>Critical Activities</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Add spacing
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Create two columns for charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Anomaly Rate Donut Chart
        anomaly_data = pd.DataFrame({
            'Category': ['Anomaly', 'Normal'],
            'Count': [anomaly_rate, 100 - anomaly_rate]
        })
        
        donut = alt.Chart(anomaly_data).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(
                field="Category",
                type="nominal",
                scale=alt.Scale(
                    domain=['Anomaly', 'Normal'],
                    range=['#191970', '#87CEFB']
                )
            )
        ).properties(
            title={
                "text": f"Anomaly Rate: {anomaly_rate:.1f}%",
                "color": "#191970",
                "fontSize": 16
            },
            width=300,
            height=300
        )
        
        st.altair_chart(donut, use_container_width=True)
    
    with chart_col2:
        # Behavior Distribution Chart
        behavior_data = pd.DataFrame({
            'Behavior': ['Normal', 'Suspicious', 'Critical'],
            'Count': [
                len(department_data[department_data['Behavior_Label'] == 'Normal']),
                suspicious_count,
                critical_count
            ]
        })
        
        behavior_chart = alt.Chart(behavior_data).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color(
                field="Behavior",
                type="nominal",
                scale=alt.Scale(
                    domain=['Normal', 'Suspicious', 'Critical'],
                    range=['#87CEFB', '#191970', '#4169E1']
                )
            )
        ).properties(
            title={
                "text": "Behavior Distribution",
                "color": "#191970",
                "fontSize": 16
            },
            width=300,
            height=300
        )
        
        st.altair_chart(behavior_chart, use_container_width=True)
    
    # Calculate and display overall department status
    if critical_count > 0.2 * total_employees:
        status = 'Poor'
        status_color = '#191970'
    elif suspicious_count > 0.1 * total_employees:
        status = 'Neutral'
        status_color = '#4169E1'
    else:
        status = 'Normal'
        status_color = '#87CEFB'
    
    # Overall status card at the bottom
    st.markdown(f"""
        <div style="background-color:{status_color};padding:20px;border-radius:10px;text-align:center;color:white;font-size:24px;margin-top:25px;">
            Overall Department Status: {status}
        </div>
    """, unsafe_allow_html=True)

    # Get employee data and validate behavior
    employee_data = employee_df[employee_df['Employee_ID'] == selected_id].iloc[0]
    employee_behavior = validate_employee_behavior(selected_id, employee_df, autoencoder)

    # Convert timestamps
    employee_data['Login_Timestamp'] = pd.to_datetime(employee_data['Login_Timestamp'])
    employee_data['Logout_Timestamp'] = pd.to_datetime(employee_data['Logout_Timestamp'])
    session_duration = (employee_data['Logout_Timestamp'] - employee_data['Login_Timestamp']).total_seconds() / 3600

    # Behavior Alert
    if employee_behavior:
        behavior_label = employee_behavior['Behavior_Label']
        alert_html = {
            'Normal': '<div class="status-box normal">✅ Normal Behavior: All activities within expected patterns</div>',
            'Suspicious': '<div class="status-box suspicious">⚠️ Suspicious Activity: Unusual patterns detected</div>',
            'Critical': '<div class="status-box critical">🚨 Critical Alert: Confirmed irregular behavior</div>'
        }
        st.markdown(alert_html.get(behavior_label, ''), unsafe_allow_html=True)

    # KPI Cards
    st.markdown("""
        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-title">Session Duration</div>
                <div class="kpi-value">{:.2f} hrs</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Idle Time</div>
                <div class="kpi-value">{:.2f} hrs</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">File Access</div>
                <div class="kpi-value">{}</div>
            </div>
        </div>
    """.format(session_duration, employee_data['Idle_Time'], employee_data['File_Access_Frequency']), unsafe_allow_html=True)

    # Employee Information Card
    # Employee Information Card
    st.markdown("""
        <div class="employee-card">
            <div class="employee-header">Employee Information</div>
            <div class="employee-info">
                <div class="info-item">
                    <div class="info-label">Employee ID</div>
                    <div class="info-value">{}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Department</div>
                    <div class="info-value">{}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Role</div>
                    <div class="info-value">{}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">VPN Usage</div>
                    <div class="info-value">{}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Login Time</div>
                    <div class="info-value">{}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Logout Time</div>
                    <div class="info-value">{}</div>
                </div>
            </div>
        </div>
    """.format(
        employee_data['Employee_ID'],
        employee_data['Department'],
        employee_data['Role'],
        employee_data['VPN_Usage'],
        employee_data['Login_Timestamp'].strftime('%I:%M %p'),  # 12-hour format with AM/PM
        employee_data['Logout_Timestamp'].strftime('%I:%M %p')  # 12-hour format with AM/PM
    ), unsafe_allow_html=True)

    # Activity Graphs
    st.markdown("<h2 style='color: #191970; margin-top: 2rem;'>📈 Activity Analysis</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Daily Activity Pattern</div>', unsafe_allow_html=True)
        peak_hours_chart = create_peak_hours_chart(employee_df[employee_df['Employee_ID'] == selected_id])
        st.altair_chart(peak_hours_chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Employee Behaviour Metrics</div>', unsafe_allow_html=True)
        comparison_chart = create_behavior_comparison_chart(
            employee_df[employee_df['Employee_ID'] == selected_id],
            department_employees,
            ['Work_Duration', 'Idle_Time', 'File_Access_Frequency', 'VPN_Usage']
        )
        st.altair_chart(comparison_chart, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    

if __name__ == "__main__":
    main()
