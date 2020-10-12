import math
import pandas as pd
import numpy as np
import world_bank_data as wb
import country_converter as coco
import re

base_path = "./DATA/"
JHU_path  = base_path + "JHU_data/"
pop_path  = base_path + "Population_data/"

def read_demographic_data_of_chinese_provinces():
    file = open(pop_path + 'china_population_wiki.tsv', 'r')

    lines = []
    for i, text in enumerate(file.readlines()):
        if i % 3 == 0:
            line = ''
        line += text.strip()
        if i % 3 == 2:
            lines = lines + [line.split('\t')]

    df             = pd.DataFrame.from_records(lines).iloc[:, [1, 2, 4, 5, 6, 7]]
    df.columns     = ['ISO', 'Province_Orig', 'Capital', 'Population', 'Density', 'Area']
    df.Population  = [int(re.sub(',|\[8\]', '', p)) for p in df.Population]
    df['Province'] = [re.sub("Province.*|Municipality.*|Autonomous.*|Zhuang.*|Special.*|Hui|Uyghur", "", s).strip() \
                      for s in df['Province_Orig']]

    return df.sort_values('Province')

def add_countries_population(data):
    d = data.copy()

    populations = wb.get_series('SP.POP.TOTL', date='2018', id_or_value='id', simplify_index=True)
    countries   = d['Country'].unique()
    IOS3_codes  = coco.convert(list(countries), to='ISO3')
    ISO3_map    = dict(zip(countries, IOS3_codes))
    d.insert(4, 'Population', [populations[c] if c in populations else 0 for c in [ISO3_map[country] for country in d.Country]])

    return d

def add_regions_population(data):
    d = data.copy()

    # China
    pop_CHI = read_demographic_data_of_chinese_provinces().set_index('Province')['Population']
    ind     = (d.Country == 'China') & (d.State != '<all>')
    d.loc[ind, 'Population'] = [pop_CHI[p] if p in pop_CHI else 0 for p in d.loc[ind, 'State']]

    # Australia
    pop_AUS = pd.read_csv(pop_path + "population_australia_states.csv")
    ind     = (d.Country == 'Australia') & (d.State != '<all>')
    d.loc[ind, 'Population'] = [pop_AUS.Population[pop_AUS.State == p].values[0] for p in d.loc[ind, 'State']]

    # Canada
    pop_CAN = pd.read_csv(pop_path + "population_canada_states.csv")
    ind     = (d.Country == 'Canada') & (d.State != '<all>')
    d.loc[ind, 'Population'] = [pop_CAN.Population[pop_CAN.State == p].values[0] for p in d.loc[ind, 'State']]

    return d


def loadData_regions(fileName, columnName):
    data = pd.read_csv(JHU_path + fileName) \
             .rename(columns={'Country/Region':'Country', 'Province/State':'State' }) \
             .melt(id_vars=['Country', 'State', 'Lat', 'Long'], var_name='date', value_name=columnName) \
             .astype({'date':'datetime64[ns]', columnName:'Int64'}, errors='ignore')

    # Extract chinese provinces separately.
    data_CHI = data[data.Country == 'China']

    ind = []
    for i in range(len(data.State)):
        if type(data.State.values[i]) != type(""):
            ind.append(i)
    data = data.drop(data.index[ind])

    return pd.concat([data, data_CHI])


def loadData_countries(fileName, columnName):
    agg_dict = {columnName:sum, 'Lat':np.median, 'Long':np.median}
    data = pd.read_csv(JHU_path + fileName) \
             .rename(columns={ 'Country/Region':'Country', 'Province/State':'State' }) \
             .melt(id_vars=['Country', 'State', 'Lat', 'Long'], var_name='date', value_name=columnName) \
             .astype({'date':'datetime64[ns]', columnName:'Int64'}, errors='ignore')

    data = data.groupby(['Country', 'date']).agg(agg_dict).reset_index()
    data['State'] = '<all>'

    return pd.concat([data])

def loadData_US(fileName, columnName, addPopulation=False):
    id_vars  = ['Country', 'State', 'Lat', 'Long']
    agg_dict = {columnName:sum, 'Lat':np.median, 'Long':np.median}

    if addPopulation:
        id_vars.append('Population')
        agg_dict['Population'] = sum

    data = pd.read_csv(JHU_path + fileName).iloc[:, 6:] \
             .drop('Combined_Key', axis=1) \
             .rename(columns={ 'Country_Region':'Country', 'Province_State':'State', 'Long_':'Long' }) \
             .melt(id_vars=id_vars, var_name='date', value_name=columnName) \
             .astype({'date':'datetime64[ns]', columnName:'Int64'}, errors='ignore') \
             .groupby(['Country', 'State', 'date']).agg(agg_dict).reset_index()

    return data

def loadData_Brasil():
    data_brazil = pd.read_csv(base_path + "data_brazil.csv", sep=";")

    data_brazil = data_brazil.rename(columns={"regiao": 'Country'})
    data_brazil["Country"] = ["Brazil"] * len(data_brazil["Country"])
    data_brazil = data_brazil.rename(columns={"estado": 'State'})
    data_brazil = data_brazil.rename(columns={"data": 'date'})
    data_brazil.date = [np.datetime64(data_brazil["date"][i]) \
                        for i in range(len(data_brazil))]

    populations = pd.read_csv(pop_path + "population_brazil_states.csv")

    data_brazil.insert(3, 'Lat', [-1] * len(data_brazil))
    data_brazil.insert(4, 'Long', [-1] * len(data_brazil))
    data_brazil.insert(5, 'Population', [-1] * len(data_brazil))

    for i in range(len(data_brazil)):
        ind = np.where(populations["State"] == data_brazil["State"][i])[0][0]
        with pd.option_context('mode.chained_assignment', None):
            data_brazil.Population[i] = populations["Population"][ind]

    del data_brazil["casosNovos"]
    data_brazil = data_brazil.rename(columns={"casosAcumulados": "CumConfirmed"})
    del data_brazil["obitosNovos"]
    data_brazil = data_brazil.rename(columns={"obitosAcumulados": "CumDeaths"})

    data_brazil = data_brazil.astype({"CumConfirmed": 'Int64', "CumDeaths": 'Int64', "Population": 'Int64'})

    return data_brazil

def loadData_Italy():
    data_italy = pd.read_json(base_path + 'dpc-covid19-ita-regioni.json')

    data_italy["Country"]    = ["Italy"] * len(data_italy["data"])
    data_italy["Population"] = [0.0] * len(data_italy["data"])

    data_italy = data_italy.rename(columns={"data": 'date'})
    data_italy = data_italy.rename(columns={"denominazione_regione": 'State'})
    data_italy = data_italy.rename(columns={"totale_casi": 'CumConfirmed'})
    data_italy = data_italy.rename(columns={"deceduti": 'CumDeaths'})
    data_italy = data_italy.rename(columns={"long": 'Long'})
    data_italy = data_italy.rename(columns={"lat": 'Lat'})

    del data_italy["stato"]
    del data_italy["codice_regione"]
    del data_italy["ricoverati_con_sintomi"]
    del data_italy["terapia_intensiva"]
    del data_italy["totale_ospedalizzati"]
    del data_italy["isolamento_domiciliare"]
    del data_italy["variazione_totale_positivi"]
    del data_italy["dimessi_guariti"]
    del data_italy["tamponi"]
    del data_italy["casi_testati"]
    del data_italy["note_it"]
    del data_italy["note_en"]
    del data_italy["nuovi_positivi"]
    del data_italy["totale_positivi"]

    data_italy.date = [np.datetime64(data_italy["date"][i][:10]) \
                            for i in range(len(data_italy))]

    population_italy = [(125666, 0.08, 'Valle d\'Aosta', 100,'',''),
                        (4356406, 0.08, 'Piemonte', 100,'',''),
                        (1550640, 0.08, 'Liguria', 100,'',''),
                        (10060574, 0.2, 'Lombardia', 2000,'',''),
                        (4905854, 0.08, 'Veneto', 100,'',''),
                        (1215220, 0.08, 'Friuli Venezia Giulia', 100,'',''),
                        (531178, 0.08, 'P.A. Bolzano', 100,'',''),
                        (541098, 0.08, 'P.A. Trento', 100,'',''),
                        (4459477, 0.08, 'Emilia-Romagna', 100,'',''),
                        (3729641, 0.08, 'Toscana', 100,'',''),
                        (882015, 0.08, 'Umbria', 100,'',''),
                        (1525271, 0.08, 'Marche', 100,'',''),
                        (1311580, 0.08, 'Abruzzo', 100,'',''),
                        (5879082, 0.08, 'Lazio', 5000,'',''),
                        (5801692, 0.08, 'Campania', 100,'',''),
                        (562869, 0.08, 'Basilicata', 100,'',''),
                        (305617, 0.08, 'Molise', 100,'',''),
                        (4029053, 0.08, 'Puglia', 100,'',''),
                        (1947131, 0.08, 'Calabria', 100,'',''),
                        (4999891, 0.08, 'Sicilia', 2000,'',''),
                        (1639591, 0.08, 'Sardegna', 100,'','')]

    for i in range(len(data_italy["State"])):
        for j in range(len(population_italy)):
            if data_italy["State"][i] == population_italy[j][2]:
                with pd.option_context('mode.chained_assignment', None):
                    data_italy.Population[i] = float(population_italy[j][0])

    data_italy = data_italy.astype({"CumConfirmed": 'Int64', "CumDeaths": 'Int64', "Population": 'float64'})
    data_italy = data_italy[["Country", "State", "date", "Lat", "Long", "Population", "CumConfirmed", "CumDeaths"]]

    return data_italy

def loadData():
    data_countries = loadData_countries("time_series_covid19_confirmed_global.csv", "CumConfirmed") \
        .merge(loadData_countries("time_series_covid19_deaths_global.csv", "CumDeaths"))
    data_countries = add_countries_population(data_countries)

    data_regions   = loadData_regions("time_series_covid19_confirmed_global.csv", "CumConfirmed") \
        .merge(loadData_regions("time_series_covid19_deaths_global.csv", "CumDeaths"))
    data_regions   = add_regions_population(data_regions)
    data_US        = loadData_US("time_series_covid19_confirmed_US.csv", "CumConfirmed") \
        .merge(loadData_US("time_series_covid19_deaths_US.csv", "CumDeaths", addPopulation=True))
    data_Brasil    = loadData_Brasil()
    data_Italy     = loadData_Italy()

    data = pd.concat([data_countries, data_US, data_Brasil, data_Italy, data_regions])

    return data
