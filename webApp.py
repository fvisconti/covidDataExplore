import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
alt.renderers.enable(embed_options={'theme': 'quartz'})

def fetch_all_series():
    df = pd.DataFrame()
    url = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv"
    cols = ["data","denominazione_regione", "ingressi_terapia_intensiva", "deceduti",
     "nuovi_positivi", "tamponi", "casi_testati", "ricoverati_con_sintomi"]
    iter_csv = pd.read_csv(url, iterator=True, chunksize=1000, parse_dates=['data',], usecols=cols)
    df = pd.concat([chunk[chunk['data'] > '2020-12-02'] for chunk in iter_csv])

    df.reset_index(drop=True, inplace=True)
    df.sort_values(by=['data'])

    df['nuovi_decessi'] = df.groupby('denominazione_regione')['deceduti'].apply(lambda x: x.diff().fillna(0))    
    df['nuovi_tamponi'] = df.groupby('denominazione_regione')['tamponi'].apply(lambda x: x.diff().fillna(0))
    # df['nuovi_testati'] = df.groupby('denominazione_regione')['casi_testati'].apply(lambda x: x.diff().fillna(0))

    # df['nuovi_testati'] = df['nuovi_testati'].clip(lower=0)
    df['nuovi_tamponi'] = df['nuovi_tamponi'].clip(lower=0)

    df['positivity_rate'] = np.round(df['nuovi_positivi'] / df['nuovi_tamponi'], 2)

    df.drop(df[df.data < '2020-12-03'].index, inplace=True)
    df.reset_index(drop=True, inplace=True)

    return df

def altPlotNewICU(df: pd.DataFrame, save_chart=False):
    
    tiChart = alt.Chart(df).mark_line().encode(
        alt.X('data:T', title=None),
        alt.Y('rolling_mean:Q', title=None),
        color=alt.Color('denominazione_regione:N', legend=None, scale=alt.Scale(scheme='dark2')),
        facet=alt.Facet('denominazione_regione:N', columns=4, title=None),
        tooltip=[alt.Tooltip('ingressi_terapia_intensiva:Q', title='Ingressi TI')]
    ).properties(
        width=160,
        height=90,
        title='Terapie intensive: nuovi ingressi'
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    ).configure_title(
        color='gray',
        fontSize=24,
    ).configure_line(
        size=4
    ).transform_window(
        rolling_mean='mean(ingressi_terapia_intensiva)',
        frame=[-1, 1],
        groupby=['denominazione_regione']
    )

    if save_chart:
        tiChart.save('newTI.png', scale_factor=2.0)

    return tiChart

def altPlotNewDeaths(df: pd.DataFrame, save_chart=False):
    dChart = alt.Chart(df[df['denominazione_regione'] != 'Molise']).mark_line().encode(
        alt.X('data:T', title=None),
        alt.Y('rolling_mean:Q', title=None),
        color=alt.Color('denominazione_regione:N', legend=None, scale=alt.Scale(scheme='dark2')),
        facet=alt.Facet('denominazione_regione:N', columns=4, title=None),
        tooltip=[alt.Tooltip('nuovi_decessi:Q', title='Nuovi decessi')]
    ).properties(
        width=160,
        height=90,
        title='Nuovi decessi'
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    ).configure_title(
        color='gray',
        fontSize=24,
    ).configure_line(
        size=4
    ).transform_window(
        rolling_mean='mean(nuovi_decessi)',
        frame=[-1, 1],
        groupby=['denominazione_regione']
    )

    if save_chart:
        dChart.save('newDeaths.png', scale_factor=2.0)

    return dChart

def altPlotCumDeaths(df: pd.DataFrame):
    cumDeaths = df.groupby('denominazione_regione')['deceduti'].max().to_frame().reset_index()
    chart = alt.Chart(cumDeaths).mark_bar().encode(
        x = 'deceduti:Q',
        y = alt.Y('denominazione_regione:N', sort='-x'),
        tooltip = ['deceduti']
        # color=alt.Color('denominazione_regione:N', legend=None, scale=alt.Scale(scheme='dark2')),
    ).properties(
        width=800,
        height=450,
        title='Decessi cumulati'
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    ).configure_title(
        color='gray',
        fontSize=24,
    )

    return chart

def altPosRate(df: pd.DataFrame):
    prChart = alt.Chart(df).mark_line().encode(
        alt.X('data:T', title=None),
        alt.Y('positivity_rate:Q', axis=alt.Axis(format='%'), title=None),
        color=alt.Color('denominazione_regione:N', legend=None, scale=alt.Scale(scheme='dark2')),
        facet=alt.Facet('denominazione_regione:N', columns=4, title=None),
        tooltip=[alt.Tooltip('positivity_rate:Q', title='Tasso positivi al tampone')]
    ).properties(
        width=160,
        height=90,
        title='Tasso di positivi al tampone'
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    ).configure_title(
        color='gray',
        fontSize=24,
    ).configure_line(
        size=4
    )
    # .transform_window(
    #     rolling_mean='mean(positivity_rate)',
    #     frame=[-1, 1],
    #     groupby=['denominazione_regione']
    # )

    return prChart

def main():
    
    st.title("Monitoraggio TI e decessi su base regionale")

    df = fetch_all_series()

    altICUChart = altPlotNewICU(df[df['denominazione_regione'] != 'Molise'])
    altDChart = altPlotNewDeaths(df[df['denominazione_regione'] != 'Molise'])
    altPrChart = altPosRate(df[df['denominazione_regione'] != 'Molise'])
    # cumDchart = altPlotCumDeaths(df)

    df.drop(columns=['deceduti', 'nuovi_tamponi'], axis=1, inplace=True)

    st.write(df)
    st.altair_chart(altICUChart)
    st.altair_chart(altDChart)
    st.altair_chart(altPrChart)
    # st.altair_chart(cumDchart)

if __name__ == "__main__":
    main()
