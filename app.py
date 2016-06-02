import pandas as pd
import quandl

import requests, zipfile, StringIO

def get_metadata():
    metafile_url = 'https://www.quandl.com/api/v3/databases/WIKI/codes'
    r = requests.get(metafile_url, stream=True)
    with zipfile.ZipFile(StringIO.StringIO(r.content)) as z:
        
        assert len(z.namelist()) == 1
        metafile = z.open(z.namelist()[0])
        meta = pd.read_csv(metafile, header=None, names=['code', 'descrip'])
        companylookup = [ (descrip[0:descrip.find(' Prices')], code.split('/')[-1]) 
                for code, descrip in zip(meta.code, meta.descrip) ]
        
        # compile final database accounting for exceptions
        db = {}
        for company, ticker in companylookup:
            if company[-1] != ')':
                company = company + (' (%s)' % ticker)
            
            db[company] = ticker
        return db
    
    return None

from bokeh.plotting import figure, output_file, show
from bokeh.embed import components
from math import log10
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

def build_graph_all(ticker):
    # make a graph of full range of closing prices

    # Create some data for our plot.
    data = quandl.get('WIKI/' + ticker)
    
    x = data.index  # datatime formatted
    y = data['Close']  # closing prices

    logymin, logymax = int(log10(y.min())), int(log10(y.max()))+1

    # Create a heatmap from our data.
    plot = figure(title='Data from Quandle WIKI set',
              x_axis_label='date',
              x_axis_type='datetime',
              y_axis_type="log",
              y_range=(10**logymin, 10**logymax))

    plot.line(x, y, color='navy', alpha=0.5)

    script, div = components(plot)

    return script, div

def build_graph(ticker):
    # make a graph of closing prices from previous month

    # Create some data for our plot.
    data = quandl.get('WIKI/' + ticker)
    
    # graph last month's data
    enddate = date.today() - timedelta(1)
    startdate = enddate - relativedelta(months=1)
    wdata = data[startdate:enddate]

    x = wdata.index  # datatime formatted
    y = wdata['Close']  # closing prices

    # Create a heatmap from our data.
    plot = figure(title='Data from Quandle WIKI set',
              x_axis_label='date',
              x_axis_type='datetime',
              y_axis_label='price')

    plot.line(x, y, color='navy', alpha=0.5)

    script, div = components(plot)

    return script, div


from flask import Flask, render_template, request, jsonify, redirect, url_for

app = Flask(__name__)

db = get_metadata()
defaultheader = "Company Stock to graph"

@app.route('/')
def render_root():
    return render_template('input.html', header = defaultheader)

@app.route('/autocomplete', methods=['GET'])
def autocomplete():
    search = request.args.get('q')
    results = [k for k in db.keys() if k.lower().find(search) != -1]
    return jsonify(matching_results=results)


@app.route('/graph', methods=['GET', 'POST'])
def graphCompany(company=None):
    if request.method == 'POST':

        company = (request.form['company'])
        
        if company not in db.keys():
            header = "%s not in database.<br>Reinput company to graph" % company 
            return render_template('input.html', header=header)

        ticker = db[company]

        script, div = build_graph(ticker)
        return render_template('graph.html', script=script, div=div, 
        ticker=ticker)

    else:
        return render_template('input.html', header = defaultheader)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
    #app.run(port=33507)
