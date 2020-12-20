import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
alt.renderers.enable(embed_options={'theme': 'quartz'})

def fetch_all_series():
    df = pd.DataFrame()
    url = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/dpc-covid19-ita-regioni.csv"
    cols = ["data","denominazione_regione", "ingressi_terapia_intensiva", "deceduti"]
    iter_csv = pd.read_csv(url, iterator=True, chunksize=1000, parse_dates=['data',], usecols=cols)
    df = pd.concat([chunk[chunk['data'] > '2020-12-02'] for chunk in iter_csv])

    df.reset_index(drop=True, inplace=True)
    df.sort_values(by=['data'])

    df['nuovi_decessi'] = df.groupby('denominazione_regione')['deceduti'].apply(lambda x: x.diff().fillna(0))    
    
    df.drop(df[df.data < '2020-12-03'].index, inplace=True)
    df.reset_index(drop=True, inplace=True)

    df['3dma_ti'] = df.groupby('denominazione_regione')['ingressi_terapia_intensiva'].transform(lambda x: x.rolling(window=3, min_periods=2, center=True).mean())
    df['3dma_deaths'] = df.groupby('denominazione_regione')['nuovi_decessi'].transform(lambda x: x.rolling(window=3, min_periods=2, center=True).mean())

    return df

def altPlotNewICU(df: pd.DataFrame):
    
    tiChart = alt.Chart(df).mark_line().encode(
        alt.X('data:T', title=None),
        alt.Y('3dma_ti:Q', title=None),
        color=alt.Color('denominazione_regione:N', legend=None, scale=alt.Scale(scheme='dark2')),
        facet=alt.Facet('denominazione_regione:N', columns=4, title=None),
    ).properties(
        width=160,
        height=90,
        title='Terapie intensive: nuovi ingressi su base regionale'
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    ).configure_title(
        color='gray',
        fontSize=24,
    )

    tiChart.save('newTI.png', scale_factor=2.0)

    return tiChart

def altPlotNewDeaths(df: pd.DataFrame):
    dChart = alt.Chart(df[df['denominazione_regione'] != 'Molise']).mark_line().encode(
        alt.X('data:T', title=None),
        alt.Y('3dma_deaths:Q', title=None),
        color=alt.Color('denominazione_regione:N', legend=None, scale=alt.Scale(scheme='dark2')),
        facet=alt.Facet('denominazione_regione:N', columns=4, title=None),
    ).properties(
        width=160,
        height=90,
        title='Nuovi decessi su base regionale'
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    ).configure_title(
        color='gray',
        fontSize=24,
    )

    dChart.save('newDeaths.png', scale_factor=2.0)

    return dChart

def altPlotCumDeaths(df: pd.DataFrame):
    cumDeaths = df.groupby('denominazione_regione')['deceduti'].max().to_frame().reset_index()
    chart = alt.Chart(cumDeaths).mark_bar().encode(
        x = 'deceduti:Q',
        y = alt.Y('denominazione_regione:N', sort='-x'),
        # color=alt.Color('denominazione_regione:N', legend=None, scale=alt.Scale(scheme='dark2')),
    ).properties(
        width=800,
        height=450,
        title='Decessi cumulati su base regionale'
    ).configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False
    ).configure_title(
        color='gray',
        fontSize=24,
    )

    return chart

def main():
    
    st.title("Terapie intensive: nuovi ingressi su base regionale")

    df = fetch_all_series()

    altICUChart = altPlotNewICU(df[df['denominazione_regione'] != 'Molise'])
    altDChart = altPlotNewDeaths(df[df['denominazione_regione'] != 'Molise'])
    # cumDchart = altPlotCumDeaths(df)

    df.drop(columns=['deceduti', '3dma_ti', '3dma_deaths'], axis=1, inplace=True)

    st.write(df)
    st.altair_chart(altICUChart)
    st.altair_chart(altDChart)
    # st.altair_chart(cumDchart)

if __name__ == "__main__":
    main()
