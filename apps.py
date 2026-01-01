import streamlit as st
import pandas as pd

# --- 1. Page Configuration ---
st.set_page_config(page_title="Court Hardware Dashboard", layout="wide")

# ==========================================
# 🔒 PASSWORD PROTECTION SECTION
# ==========================================
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        # ----------------------------------------------------
        # CHANGE YOUR PASSWORD HERE:
        if st.session_state["password"] == "court2026": 
        # ----------------------------------------------------
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # clean up
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.text_input(
            "Please enter the dashboard password:", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show input again.
        st.text_input(
            "Please enter the dashboard password:", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 Password incorrect")
        return False
    else:
        # Password correct.
        return True

if check_password():
    # ==========================================
    # 🚀 MAIN DASHBOARD CODE STARTS HERE
    # ==========================================

    # --- 2. CSS Styling ---
    st.markdown("""
    <style>
    /* Material 3 Card Container */
    .metric-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow:
            0px 1px 2px rgba(0, 0, 0, 0.08),
            0px 2px 6px rgba(0, 0, 0, 0.04);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
        height: 100%;
    }

    .metric-card:hover {
        box-shadow:
            0px 2px 4px rgba(0, 0, 0, 0.12),
            0px 6px 12px rgba(0, 0, 0, 0.08);
        transform: translateY(-1px);
    }

    /* Material Typography */
    .card-title {
        color: #5f6368;
        font-size: 13px;
        font-weight: 500;
        line-height: 1.4;
        margin-bottom: 6px;
    }

    .card-value {
        color: #1f1f1f;
        font-size: 20px;
        font-weight: 600;
        line-height: 1.3;
        margin-bottom: 10px;
    }

    /* Material 3 Badge (Assist Chip style) */
    .badge {
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 500;
        line-height: 1.2;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        white-space: nowrap;
    }

    .badge-green {
        background-color: #e6f4ea;
        color: #137333;
    }

    .badge-red {
        background-color: #fce8e6;
        color: #b3261e;
    }

    .badge-grey {
        background-color: #f1f3f4;
        color: #444746;
    }
</style>

    """, unsafe_allow_html=True)

    # --- 3. Data Loading ---
    @st.cache_data
    def load_data():
        file_path = 'data.xlsx'
        
        try:
            # Load the Tooli sheet
            df = pd.read_excel(file_path, sheet_name='Tooli')
            
            # 1. Clean Column Headers
            df.columns = df.columns.str.strip()
            
            # 2. Clean String Columns (Crucial for filtering)
            string_cols = ['State', 'Session_Division', 'Location_Name', 'Location_Type', 'Hardware_Item', 'Status']
            for col in string_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            # 3. Fill Missing State/Division (Forward Fill)
            if 'State' in df.columns:
                df['State'] = df['State'].replace('nan', pd.NA).ffill()
            if 'Session_Division' in df.columns:
                df['Session_Division'] = df['Session_Division'].replace('nan', pd.NA).ffill()

            # 4. Ensure Numeric Columns
            cols_to_numeric = [
                'Required_Qty', 'Distributed_Qty', 'Balance_Qty', 
                'Courts_Count', 'Family_Courts', 'TJOs', 'Total_Courts'
            ]
            for col in cols_to_numeric:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
            return df
        except Exception as e:
            st.error(f"Error loading data: {e}")
            return None

    df = load_data()

    # --- 4. Helper Function to Render Cards ---
    def render_card(title, value_top, value_bottom, balance):
        # Determine Badge Color
        if balance > 0:
            badge_class = "badge-green"
            status_text = "Surplus"
        elif balance < 0:
            badge_class = "badge-red"
            status_text = "Shortfall"
        else:
            badge_class = "badge-grey"
            status_text = "Balanced"

        # HTML Structure
        html_code = f"""
        <div class="metric-card">
            <div class="card-title">{title}</div>
            <div class="card-value">{int(value_top)} / {int(value_bottom)}</div>
            <span class="badge {badge_class}">{status_text}: {int(abs(balance))}</span>
        </div>
        """
        st.markdown(html_code, unsafe_allow_html=True)

    # --- 5. Main App Layout ---
    st.title("🏛️ Court Hardware Inventory Dashboard")

    if df is not None and not df.empty:
        
        # --- Sidebar Filters ---
        st.sidebar.header("🔍 Filters")
        
        # State Filter
        if 'State' in df.columns:
            unique_states = ['All States'] + sorted(df['State'].unique().tolist())
            selected_state = st.sidebar.selectbox("Select State", unique_states)
            
            if selected_state != 'All States':
                state_df = df[df['State'] == selected_state]
            else:
                state_df = df
        else:
            state_df = df

        # Location Selector
        if 'Location_Name' in state_df.columns:
            unique_locations = sorted(state_df['Location_Name'].unique().tolist())
            location_options = ['📊 Overall Summary'] + unique_locations
            selected_location = st.selectbox("Select Location", location_options)

            st.markdown("---")

            # =========================================================
            # VIEW 1: AGGREGATED SUMMARY
            # =========================================================
            if selected_location == '📊 Overall Summary':
                st.header(f"Aggregated Status: {selected_state}")
                
                # --- 1. Calculate Aggregated Court Counts ---
                unique_locs_df = state_df.drop_duplicates(subset=['Location_Name'])
                
                total_reg = unique_locs_df['Courts_Count'].sum()
                total_fam = unique_locs_df['Family_Courts'].sum()
                total_tjo = unique_locs_df['TJOs'].sum()
                
                if 'Total_Courts' in unique_locs_df.columns and unique_locs_df['Total_Courts'].sum() > 0:
                    total_all = unique_locs_df['Total_Courts'].sum()
                else:
                    total_all = total_reg + total_fam + total_tjo
                
                # Display Top Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("Total Courts", int(total_all))
                m2.metric("Regular Courts", int(total_reg))
                m3.metric("Family Courts", int(total_fam))
                m4.metric("TJOs", int(total_tjo))
                
                st.markdown("---")
                st.subheader("Hardware Breakdown")
                
                # --- 2. Hardware Cards ---
                summary_df = state_df.groupby('Hardware_Item')[['Required_Qty', 'Distributed_Qty', 'Balance_Qty']].sum().reset_index()
                
                cols = st.columns(4)
                for index, row in summary_df.iterrows():
                    with cols[index % 4]:
                        render_card(
                            title=row['Hardware_Item'],
                            value_top=row['Distributed_Qty'],
                            value_bottom=row['Required_Qty'],
                            balance=row['Balance_Qty']
                        )

            # =========================================================
            # VIEW 2: SPECIFIC LOCATION DETAIL
            # =========================================================
            else:
                loc_data = state_df[state_df['Location_Name'] == selected_location]
                
                if not loc_data.empty:
                    # 1. Metadata & Court Counts
                    meta = loc_data.iloc[0]
                    loc_type = meta.get('Location_Type', 'N/A')
                    
                    c_reg = int(meta.get('Courts_Count', 0))
                    c_fam = int(meta.get('Family_Courts', 0))
                    c_tjo = int(meta.get('TJOs', 0))
                    c_total = int(meta.get('Total_Courts', c_reg + c_fam + c_tjo))
                    
                    # Header Info Bar
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.info(f"**Type:** {loc_type}")
                    c2.warning(f"**Total Cts:** {c_total}")
                    c3.warning(f"**Reg. Courts:** {c_reg}")
                    c4.warning(f"**Family Cts:** {c_fam}")
                    c5.warning(f"**TJOs:** {c_tjo}")

                    # 2. Hardware Cards
                    st.subheader(f"Hardware Status: {selected_location}")
                    cols = st.columns(4)
                    
                    for index, (i, row) in enumerate(loc_data.iterrows()):
                        with cols[index % 4]:
                            render_card(
                                title=row['Hardware_Item'],
                                value_top=row['Distributed_Qty'],
                                value_bottom=row['Required_Qty'],
                                balance=row['Balance_Qty']
                            )
                    
                    # 3. Detailed Data Table
                    st.markdown("### 📋 Detailed Data")
                    cols_to_show = ['Hardware_Item', 'Required_Qty', 'Distributed_Qty', 'Balance_Qty', 'Status']
                    final_cols = [c for c in cols_to_show if c in loc_data.columns]
                    
                    def highlight_status(val):
                        if val == 'Shortfall': return 'background-color: #ffcccc; color: darkred'
                        elif val == 'Surplus': return 'background-color: #ccffcc; color: darkgreen'
                        return ''

                    if 'Status' in final_cols:
                        st.dataframe(
                            loc_data[final_cols].style.map(highlight_status, subset=['Status']),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.dataframe(loc_data[final_cols], use_container_width=True)
                else:
                    st.error(f"No data found for location: '{selected_location}'")

        else:
            st.error("Column 'Location_Name' not found in Excel file.")
    else:
        st.error("Could not load data. Please ensure 'data.xlsx' is in the folder.")