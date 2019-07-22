import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_daq as daq
import os
import io
from dash.dependencies import Input, Output, State
import base64
import urllib.parse


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(children=[
    html.Div(children=[
        html.H1(children='Merge Files'),

        html.Div(children="Merge two files based on column identity")
    ], style = {"textAlign":"center"}),
    html.Hr(),

	html.Div(children=[
        html.Label('Select if a header is present in your files or not'),
        daq.ToggleSwitch(
            id='id_switch_header',
            label=['Header', 'No Header'],
            style={'width': '250px', 'margin': 'auto'}, 
            value=False
        ),

        html.Hr(),
        html.Label('Select first file'),
        dcc.Upload(
            id="upload-f1",
            children=html.Div(['Drag and Drop or ', html.A('Select File')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            }
        ),
        html.Label(id = "msg-select1", children=""),
        dcc.Tabs(id='upload-f1-res',value=None)
    ], style = {"textAlign":"center"}),

    html.Hr(),
    html.Div(children=[
        html.Label('Select second file'),
        dcc.Upload(
            id="upload-f2",
            children=html.Div(['Drag and Drop or ', html.A('Select File')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px'
            }
        ),
        html.Label(id = "msg-select2", children=""),
        dcc.Tabs(id='upload-f2-res',value=None)
    ], style = {"textAlign":"center"}),
    html.Hr(),
    html.Div(children=[
        html.Button('Submit', id='button'),
        html.H3(id="download_common", children=""),
        html.H3(id="download_unique", children="")
        #html.Div(id="final_res", children="")
    ], style = {"textAlign":"center"}),

])


@app.callback(
            [Output('upload-f1-res',"children"),
            Output('upload-f1',"children"),
            Output('msg-select1',"children")],
            [Input('upload-f1',"contents")],
            [State('upload-f1',"filename")])
def read_header1(contents,filename):
    ''' update for first input file '''
    if contents is not None:
        msg_select = "Select the column to synchronize"
        newName = filename
        list_header_tab = treatFile(contents)
        return list_header_tab, newName, msg_select
    else:
        newName = html.Div(['Drag and Drop or ', html.A('Select File')])
        return "",newName,""

@app.callback(
            [Output('upload-f2-res',"children"),
            Output('upload-f2',"children"),
            Output('msg-select2',"children")],
            [Input('upload-f2',"contents")],
            [State('upload-f2',"filename")])
def read_header2(contents,filename):
    ''' update for second input file '''
    if contents is not None:
        msg_select = "Select the column to synchronize"
        newName = filename
        list_header_tab = treatFile(contents)
        return list_header_tab, newName, msg_select
    else:
        newName = html.Div(['Drag and Drop or ', html.A('Select File')])
        return "",newName,""

@app.callback(
            [Output("download_common","children"),
            Output("download_unique","children")],
            [Input('button',"n_clicks")],
            [State('id_switch_header',"value"),
            State('upload-f1',"filename"),
            State('upload-f1',"contents"), 
            State('upload-f1-res',"value"),
            State('upload-f2',"filename"),
            State('upload-f2',"contents"),
            State('upload-f2-res',"value")])
def getRes(n_clicks,header, filename1,content1,col1, filename2,content2,col2):
    if col1 is not None and col2 is not None:
        #print n_clicks, header, col1, col2
        dico1, h1 = createDicoColumn(content1,int(col1),header)
        #print n_clicks, header, col1, col2
        dico2, h2 = createDicoColumn(content2,int(col2),header)
        #print h1, h2
        final_common_res, final_unique_res = mergeDico(dico1,dico2,h1,h2)
        #return html.A("Download common", href=outname)#)#,html.A("Download unique", href=outname2)
        return html.A("Download common", download="common.tsv",href=final_common_res, target="_blank"),html.A("Download unique", download="unique.tsv",href=final_unique_res, target="_blank")
    else:
        return "",""




def treatFile(contents):
    #decode content 
    content_type, content_string = contents.split(',')
    #print(contents)
    decoded = (base64.b64decode(content_string)).decode('utf-8')
    #print((decoded.decode('utf-8')))
    #list_lines = decoded.split("\n")
    list_lines = decoded.split("\n")
    list_header = list_lines[0].split("\t")
    list_header_tab = []
    '''
    #Create tab formated part = list of dcc.Tab : 
    # dcc.Tab(label='Tab one', value='tab-1'),
    # dcc.Tab(label='Tab two', value='tab-2')
    '''
    for i in range(len(list_header)):
        val = str(i)
        label = list_header[i]
        list_header_tab.append(dcc.Tab(label=label, value=val))
    return list_header_tab


def createDicoColumn(contents,column_index, no_header):
    dico = {}
    content_type, content_string = contents.split(',')
    decoded = (base64.b64decode(content_string)).decode('utf-8')

    list_lines = decoded.split("\n")

    #if there is no header, all lines are read, starting from line number 0
    if no_header:
        h = None
        line_start = 0
    #if there is a header, first line is stored in variable h, and we start reading line number 1
    else:
        h = list_lines[0]
        line_start = 1

    for line in list_lines[line_start:]:
        id_line = line.split("\t")[column_index]
        dico[id_line] = line
    return dico, h


def mergeDico(dico1,dico2,h1,h2):

    common_res = ""
    unique_res = ""
    if h1 is not None:
        #print h1
        header_common = h1+"\t"+h2+"\n"
        common_res+= header_common
        header_unique = h1+"\n"
        unique_res+= header_unique

    for d in dico1:
        #print d
        if d in dico2:
            toWrite_common = dico1[d]+"\t"+dico2[d]+"\n"
            common_res+=  toWrite_common
        else:
            toWrite_unique = dico1[d]+"\n"
            unique_res+= toWrite_unique
    final_common_res = "data:text/tsv;charset=utf-8,"+urllib.parse.quote(common_res)
    final_unique_res = "data:text/tsv;charset=utf-8,"+urllib.parse.quote(unique_res)
    return final_common_res, final_unique_res
    


if __name__ == '__main__':
    app.run_server(debug=True)
