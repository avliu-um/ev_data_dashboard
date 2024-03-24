import numpy as np
import pandas as pd
import streamlit as st
import boto3

def get_s3_filepaths(bucket, prefix):
    """ Returns a list of filepaths from the specified S3 bucket and prefix """
    s3_client = boto3.client('s3')
    s3_bucket = bucket
    s3_prefix = prefix
    response = s3_client.list_objects(Bucket=s3_bucket, Prefix=s3_prefix)

    keys = [file['Key'] for file in response.get('Contents', []) if file['Key'].endswith('.csv')]
    filepaths = []
    for k in keys:
        filepath = f's3://{bucket}'
        if prefix:
            filepath += f'/{prefix}'
        filepath += f'/{k}'
        filepaths.append(filepath)
    return filepaths


# load the dataset (df)
@st.cache_data
def load_data(s3_filepath):
    df = pd.read_csv(s3_filepath)
    return df

# creates hist with bins given int/double data
# Input: dataframe column (so I guess series)
def create_hist_df(df, col, bins=20):
    alphabet = 'abcdefghijklmnopqrstuvwxyz' # hacky way of ensuring x ticks stay ordered
    hist = np.histogram(df[col].dropna().astype('int'), bins=bins)
    x_bins = [str((alphabet[tick_idx], int(hist[1][tick_idx]), int(hist[1][tick_idx+1]))) for tick_idx in range(len(hist[1])-1)] 
    y = hist[0]

    x_label = 'bins'
    y_label = 'counts'
    hist_df = pd.DataFrame({x_label:x_bins, y_label: y})
    return hist_df, x_label, y_label

# Dropdown to select the CSV file
bucket_name = 'ev-sales-public'
prefix = ''
filepaths = get_s3_filepaths(bucket_name, prefix)
selected_filepath = st.selectbox("Select a CSV file from S3:", filepaths)
df = load_data(selected_filepath)

st.markdown(f"# EV Sales dataset visualizer")
st.markdown(f"Using dataset from {selected_filepath}.")

# plots:
# price (hist), year manufactured (hist), location (map), fuel type (pi chart but hist for now)
print(f'plotting price')
price_hist_df, xl, yl = create_hist_df(df, 'offers_price')
st.subheader('Price histogram')
st.bar_chart(price_hist_df, x=xl, y=yl)

print(f'plotting year')
df['year'] = df['year'].apply(lambda x: x[:4] if type(x)==str else x)
year_hist_df, xl, yl = create_hist_df(df, 'year')
st.subheader('Manufactured year histogram')
st.bar_chart(year_hist_df, x=xl, y=yl)

print(f'plotting fuel')
fuel_hist_df = pd.DataFrame(df['fuel'].value_counts()).reset_index()
st.subheader('Fuel type histogram')
st.bar_chart(fuel_hist_df, x='fuel', y='count')

print(f'plotting location')
map_values = df[['offers_latitude', 'offers_longitude']].dropna(how='any')
st.subheader('Location map')
st.map(map_values, latitude='offers_latitude', longitude='offers_longitude')

