from flask import Flask, render_template
from database import mysql, neo4j

app = Flask(__name__)


@app.route('/')
@app.route('/home')
def hello_world():
    return render_template('home.html')


@app.route('/paper/info/<paperid>')
def paperinfo(paperid):
    p = m.getPaperInfo([paperid])[0]
    p = n.getNeighbors(p)
    refs_id = [p.refs[paper] for paper in p.refs]
    refs = m.getPaperInfo(refs_id)
    refs_full = []
    for ref in refs:
        ref_full = n.getNeighbors(ref)
        refs_full.append(ref_full)
    return render_template('paperinfo.html', paper=p, p_refs=refs_full)

@app.route('/author/info/<authorid>')
def authorinfo(authorid):
    return render_template('scholarinfo.html')

@app.route('/graphdata/<paperid>', methods=['POST'])
def loadGraph(paperid, load_type='G'):
    js = {}
    if load_type == 'G':
        p = m.getPaperInfo([paperid])[0]
        p = n.getNeighbors(p)
        refs_id = [p.refs[paper] for paper in p.refs]
        refs = m.getPaperInfo(refs_id)
        refs_full = []
        for ref in refs:
            ref_full = n.getNeighbors(ref)
            refs_full.append(ref_full)
        js = {
            "type": "force",
            "categories": [
                {
                    "name": "SOURCE"
                },
                {
                    "name": "TARGET"
                },
                {
                    "name": "AUTHOR"
                },
                {
                    "name": "KEYWORD"
                }
            ],
            "nodes": [],
            "links": []
        }
        nodes = [{
            "id": p.n_id,
            "name": p.paper_id,
            "type": "Paper",
            "symbolSize": 20,
            "category": 1,
            "label": {
                "show": True
            }
        }]
        edges = []; auths = []; kywds = []
        for author in p.authors:
            nodes.append({
                "id": author,
                "name": p.authors[author],
                "type": "Author",
                "category": 2,
                "symbolSize": 6
            })
            edges.append({
                "source": author,
                "target": p.n_id
            })
            auths.append(author)
        for keyword in p.keywords:
            nodes.append({
                "id": keyword,
                "name": p.keywords[keyword],
                "type": "Keyword",
                "category": 3,
                "symbolSize": 6
            })
            edges.append({
                "source": keyword,
                "target": p.n_id
            })
            kywds.append(keyword)
        for ref in refs_full:
            nodes.append({
                "id": ref.n_id,
                "name": ref.paper_id,
                "type": "Paper",
                "symbolSize": 20,
                "category": 0,
                "label": {
                    "show": True
                }
            })
            edges.append({
                "source": ref.n_id,
                "target": p.n_id
            })
            for author in ref.authors:
                if author in auths:
                    edges.append({
                        "source": author,
                        "target": ref.n_id
                    })
            for keyword in ref.keywords:
                if keyword in kywds:
                    edges.append({
                        "source": keyword,
                        "target": ref.n_id
                    })
        js['nodes'] = nodes
        js['links'] = edges
    print(js)
    return js


if __name__ == '__main__':
    m = mysql.mysqlConnection()
    n = neo4j.neoConnection()
    app.run(host='0.0.0.0', threaded=True)
