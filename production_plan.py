import pandas as pd
from scipy.optimize import minimize
import numpy as np
import math


def production_plan(data_load):
    # Creating a DataFrame with the plant information to which we will add cost/MWh
    # and calculate pmax base on the fuels available (for the wind)
    if not data_load:
        return [{'data': 'error'}]

    df = pd.DataFrame(data_load["powerplants"])

    # Calculation of the cost per unit (MWh) produced
    list_cost = []

    for i in range(len(data_load["powerplants"])):
        plant = data_load["powerplants"][i]
        if plant['type'] == 'gasfired':
            # The cost per mwh for a gasfired power plant is cost of gas / efficiency
            # + 0.3 (ton of CO2 rejected per mwh produced) * price of CO2/ton
            list_cost += [data_load["fuels"]["gas(euro/MWh)"] / data_load["powerplants"][i]["efficiency"] + 0.3 *
                          data_load["fuels"]["co2(euro/ton)"]]
        elif plant['type'] == 'turbojet':
            list_cost += [data_load["fuels"]["kerosine(euro/MWh)"] / data_load["powerplants"][i]["efficiency"]]
        else:
            list_cost += [0]

    # Calculation of pmax for windturbine

    df.loc[df.type == 'windturbine', 'pmax'] = df.loc[df.type == 'windturbine', 'pmax'] * data_load["fuels"][
        "wind(%)"] / 100

    df['cost_per_mwh'] = list_cost

    load = data_load['load']

    list_p = []  # contains the final p

    # function representing the total cost for given values of p (args) that we will have to minimize (our objective)
    def cost_min(args):
        sum_cost = 0
        for i in range(len(args)):
            sum_cost += args[i] * df.loc[df.index == i]['cost_per_mwh'].values[0]
        return sum_cost

    # the minimization constraint (i.e. sum of p should be equal to the load)
    def constraint(args):
        sum_p = load
        for arg in args:
            sum_p -= arg
        return sum_p

    # will be used to switch off some factories, it creates a list of all the binary number from 0 to upper
    # with length number of digit (e.g. upper =4 , length = 2 return [['0','0'],['0','1'],['1','0'],['1','1']])
    def generate_bin_count(upper, length):
        list_bin = []

        for i in range(upper):

            bits = bin(i).replace("0b", "")
            while len(bits) != length:
                bits = '0' + bits

            list_bin += [list(bits)]
        return (list_bin)

    x0 = np.zeros(len(df.index))  # Start of the minimization all p are null
    list_index_gas = df.loc[df["pmin"] != 0].index.values
    # List for switching the bounds to be 0,0 of the power plants with pmin !=0 (state turned off)
    # all possible combination of 0 and 1 => 0 off / 1 on
    switch = generate_bin_count(2 ** (len(list_index_gas)), len(list_index_gas))
    minimal_cost = math.inf # Cost initialized to +inf

    # There is 2^(number of switchable off) possibilities
    for item in switch:

        bnds = [(df.loc[df.index == i]['pmin'].values[0], df.loc[df.index == i]['pmax'].values[0])
                     for i in range(len(df.index))]

        con = {'type': 'eq', 'fun': constraint}

        # using the list of the binary number from 0 to 2^(number of plant with pmin != 0), we can set the 
        # some plants off, this way we will be able to check the best configuration
        for i in range(len(list_index_gas)):
            bnds[list_index_gas[i]] = (
                bnds[list_index_gas[i]][0] * int(item[i]), bnds[list_index_gas[i]][1] * int(item[i]))

        this_minimization = minimize(cost_min, x0, bounds=bnds, constraints=con)
        # Now we check which minimization cost the least and where the constraint (i.e. the sum of the p) is 0
        if minimal_cost > this_minimization.fun and constraint(this_minimization.x) < 0.1:
            minimal_cost = this_minimization.fun
            list_p = ['%.2f' % elem for elem in this_minimization.x]

        production_plan = []
        for i in range(len(list_p)):
            production_plan.append({
                'name': df.loc[df.index == i]['name'].values[0],
                'p': list_p[i]
            })
    return production_plan

if __name__ == '__main__':
    production_plan(data_load={})
