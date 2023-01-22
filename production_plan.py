import pandas as pd
import math
from pandas import DataFrame


def production_plan(data_load):
    # Creating a DataFrame with the plant information to which we will add cost/MWh
    # and calculate pmax base on the fuels available (for the wind)
    df: DataFrame = pd.DataFrame.from_dict(data_load['powerplants'])

    # Calculation of the cost per unit (MWh) produced
    list_cost = [0] * len(df)

    df['cost_per_mwh'] = list_cost

    df.loc[df['type'] == 'gasfired', 'cost_per_mwh'] = [data_load["fuels"]["gas(euro/MWh)"] / data["efficiency"] + 0.3 *
                                                        data_load["fuels"]["co2(euro/ton)"] for data in
                                                        data_load["powerplants"] if data["type"] == 'gasfired']

    df.loc[df['type'] == 'turbojet', 'cost_per_mwh'] = [data_load["fuels"]["kerosine(euro/MWh)"] / data["efficiency"]
                                                        for data in
                                                        data_load["powerplants"] if data["type"] == 'turbojet']

    # Calculation of pmax for windturbine

    df.loc[df.type == 'windturbine', 'pmax'] = df.loc[df.type == 'windturbine', 'pmax'] * data_load["fuels"][
        "wind(%)"] / 100

    # Reorder the data frame with growing cost/mwh

    df = df.sort_values(by=['cost_per_mwh']).reset_index()
    del df['index']

    # And we will also calculate the plim, which define the upper limit of when we need to switch to a higher cost
    # energy per mwh to lower the total cost

    df['plim'] = df['pmin']

    df_cost = df[['cost_per_mwh', 'pmin', 'plim']].drop_duplicates().reset_index()
    del df_cost["index"]

    plim_list = []
    for i in range(0, len(df_cost)):
        if df_cost.loc[i, 'cost_per_mwh'] != 0 and df_cost.loc[i - 1, 'cost_per_mwh'] != 0:
            df_cost.loc[i, 'plim'] = df_cost.loc[i - 1, 'pmin'] * df_cost.loc[i - 1, 'cost_per_mwh'] / df_cost.loc[
                i, 'cost_per_mwh']
        else:
            df_cost.loc[i, 'plim'] = math.inf
        plim_list += [df_cost.loc[i, 'plim']] * len(df.loc[df["cost_per_mwh"] == df_cost.loc[i, 'cost_per_mwh']])

    df['plim'] = plim_list

    load = data_load['load']

    list_p = []  # contains the final p

    # According to the value of the 0 cost power plant, the decision will be made of which power plant to activate next
    # in order to minimize the cost of production

    no_cost_pmax = df.loc[df['cost_per_mwh'] == 0, 'pmax'].sum()

    to_be_reached = load

    if no_cost_pmax < load:  # If the 0 cost energy is not sufficient
        # Then we have to decide which energy to take
        df2 = pd.concat([df.loc[(df['cost_per_mwh'] != 0) & (df['plim'] > load - no_cost_pmax)].sort_values(by='plim'),
                         df.loc[(df['cost_per_mwh'] != 0) & (df['plim'] < load - no_cost_pmax)]])
        df2.reset_index(inplace=True)  #
        del df2['index']

        list_p += df.loc[df['cost_per_mwh'] == 0, ['pmax', 'name']].rename(columns={'pmax': 'p'}).to_dict(
            orient='records')
        to_be_reached -= df.loc[df['cost_per_mwh'] == 0, 'pmax'].sum()
    else:  # If the 0 cost energy is sufficient
        df2 = df

    i = 0

    while i < len(df2) and to_be_reached - df2.loc[i, 'pmax'] >= 0:  # Adding pmax until the load is reached
        p = df2.loc[i, 'pmax']
        list_p += [{'p': p, 'name': df2.loc[i, 'name']}]
        to_be_reached -= p
        i += 1
    if i < len(df2) and to_be_reached < df2.loc[i, 'pmin']:
        # if the pmin is not sufficient we will take some mwh from a 0 cost source
        list_p += [{'p': df2.loc[i, 'pmin'], 'name': df2.loc[i, 'name']}]
        list_p[-2]['p'] -= list_p[-1]['p'] - to_be_reached
        j = -2
        while list_p[j]['p'] < 0 and abs(j)< len(list_p):
            list_p[j-1]['p'] += list_p[j]['p']
            list_p[j]['p'] = 0

    elif i < len(df2):
        list_p += [{'p': to_be_reached, 'name': df2.loc[i, 'name']}]

    list_p += [{
        'p': 0,
        'name': df2.loc[df2.index == i+j+1]['name'].values[0]
    } for j in range(len(df) - len(list_p))]

    ''' Dealing with the numpy.float64 types that raised some errors'''

    list_p = [{'name': item['name'], 'p': float(round(item['p'],3))} for item in list_p]

    return list_p


if __name__ == '__main__':
    production_plan(data_load={})
