import numpy as np
import pandas as pd
from os.path import join as oj
import pygsheets
import pandas as pd
import sys
sys.path.append('../modeling')
sys.path.append('..')
import load_data
from fit_and_predict import add_preds
from functions import merge_data

meanings = {
        1: 'Low',
        2: 'Moderate',
        3: 'Substantial',
        4: 'Severe',
        5: 'Critical'
    }

def add_severity_index(df, NUM_DAYS_LIST=[1, 2, 3]):
    def apply_manual_thresholds(vals, manual_thresholds = {5: 10,
                                                           4: 3,
                                                           3: 2,
                                                           2: 0.8,
                                                           1: 0}):
        new_col = vals * 0
        for key in sorted(manual_thresholds.keys()):
            new_col[vals >= manual_thresholds[key]] = key
        return new_col

    # this is number of new predicted deaths
    for num_days in NUM_DAYS_LIST:
        df[f'Predicted Deaths Hospital {num_days}-day'] = ((df[f'Predicted Deaths {num_days}-day'] - df['tot_deaths']) * df['Frac Hospital Employees of County']).fillna(0)
        df[f'Severity Percentile {num_days}-day'] = pd.qcut(df[f'Predicted Deaths Hospital {num_days}-day'], 5, labels=False) + 1
        df[f'Severity {num_days}-day'] = apply_manual_thresholds(df[f'Predicted Deaths Hospital {num_days}-day'])
        
    df[f'Predicted Deaths Hospital {0}-day'] = (df[f'tot_deaths'] * df['Frac Hospital Employees of County']).fillna(0)
    df[f'Severity {0}-day'] = apply_manual_thresholds(df[f'Predicted Deaths Hospital {0}-day'])
    #     df[f'Quantile {num_days}-day'] = 
    k = 2
    s_hosp = f'Predicted Deaths Hospital {k}-day'
    s_index = f'Severity {k}-day'
    return df.sort_values(s_hosp, ascending=False).round(2)

def write_to_gsheets(df, ks_output=['Severity 1-day', 'Severity 2-day', 'Severity 3-day', 'Severity 4-day',
                                    'Severity 5-day', 'Severity 6-day', 'Severity 7-day',
                                    'Hospital Name',
                                    'CMS Certification Number', 'countyFIPS', 'CountyName', 'StateName', 'System Affiliation'],
                     sheet_name='COVID Severity Index',
                     service_file='../creds.json'):
    print('writing to gsheets...')
    gc = pygsheets.authorize(service_file=service_file)
    sh = gc.open(sheet_name) # name of the hospital
    wks = sh[0] #select a sheet
    wks.update_value('A1', "Note: this sheet is read-only (automatically generated by the data and model)")
    wks.set_dataframe(df[ks_output], (3, 1)) #update the first sheet with df, starting at cell B2. 

if __name__ == '__main__':
    NUM_DAYS_LIST = [1, 2, 3, 4, 5, 6, 7]
    df_county = load_data.load_county_level(data_dir='../data')
    df_hospital = load_data.load_hospital_level(data_dir='../data_hospital_level')
    df_county = add_preds(df_county, NUM_DAYS_LIST=NUM_DAYS_LIST, cached_dir='../data') # adds keys like "Predicted Deaths 1-day"
    df = merge_data.merge_county_and_hosp(df_county, df_hospital)
    df = add_severity_index(df, NUM_DAYS_LIST)
    write_to_gsheets(df)
    print('success!')


