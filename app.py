from flask import Flask, render_template, request, abort, jsonify
import time
from database import mysql, neo4j
import instance.paper as pt
import re

app = Flask(__name__)


@app.route('/')
@app.route('/home')
def hello_world():
    return render_template('home.html')


@app.route('/paper/info/<paperid>')
def paperinfo(paperid):
    # p = m.getPaperInfo([paperid])[0]
    p = n.getPaperBasic(paperid)
    p = n.getNeighbors(p)
    refs_id = [p.refs[paper] for paper in p.refs]
    cits_id = [p.cits[paper] for paper in p.cits]
    recs_id = [p.recs[paper] for paper in p.recs]
    # refs = m.getPaperInfo(refs_id)
    # cits = m.getPaperInfo(cits_id)
    # recs = m.getPaperInfo(recs_id)
    refs_full = []
    for ref_id in refs_id:
        refs_full.append(n.getPaperBasic(ref_id))
    cits_full = []
    for cit_id in cits_id:
        cits_full.append(n.getPaperBasic(cit_id))
    recs_full = []
    for rec_id in recs_id[:12]:
        recs_full.append(n.getPaperBasic(rec_id))
    # refs_full = []
    # for ref in refs:
    #     ref_full = n.getNeighbors(ref)
    #     refs_full.append(ref_full)
    refs_full.sort(key=lambda ref: ref.year)
    # cits_full = []
    # for cit in cits:
    #     cit_full = n.getNeighbors(cit)
    #     cits_full.append(cit_full)
    # recs_full = []
    cits_full.sort(key=lambda cit: cit.year)
    # for rec in recs:
    #     rec_full = n.getNeighbors(rec)
    #     recs_full.append(rec_full)
    recs_full.sort(key=lambda rec: p.rec_sim[rec.n_id], reverse=True)
    authors_full = []
    for auth in p.authors:
        authors_full.append(n.getAuthorBasic(auth))
    return render_template('paperinfo.html', paper=p, p_refs=refs_full, p_cits=cits_full, auths=authors_full,
                           len_p_refs=len(refs_full), len_p_cits=len(cits_full), recs_full=recs_full)


@app.route('/author/info/<authorid>')
def authorinfo(authorid):
    author = n.getAuthorInfo(authorid)
    # 处理年份跨度
    if list(author.paper_count_year.keys())[0] == list(author.paper_count_year.keys())[-1]:
        year = list(author.paper_count_year.keys())[0]
    else:
        year = str(list(author.paper_count_year.keys())[0]) + '-' + str(list(author.paper_count_year.keys())[-1])
    i = 0
    top_keywords = []
    keyword_dict = {}
    for keyword_id in author.paper_count_keyword.keys():
        name = n.getKeyword(keyword_id)
        count = author.paper_count_keyword[keyword_id]
        if i <= 7:
            top_keywords.append([name, count])
            i += 1
        keyword_dict[name] = count
    i = 0
    author.paper_count_keyword = keyword_dict
    top_co_authors = []
    for author_id in author.co_authors.keys():
        name = n.getAuthorBasic(author_id)
        count = author.co_authors[author_id]
        top_co_authors.append([name, count])
        i += 1
        if i >= 3:
            break
    return render_template('scholarinfo.html', author=author, year=year, top_keywords=top_keywords,
                           top_co_authors=top_co_authors)


@app.route('/graphdata/<paperid>', methods=['POST'])
def loadGraph(paperid):
    load_type = request.form['load_type']
    js = {}
    if load_type == 'G':
        p = n.getPaperBasic(paperid)
        p = n.getNeighbors(p)
        cits_id = [p.cits[paper] for paper in p.cits]
        cits_full = []
        for cit_id in cits_id:
            cits_full.append(n.getPaperBasic(cit_id))
        nodes = [{
            "id": p.n_id,
            "name": p.paper_id,
            "type": "Paper",
            "title": p.title,
            "year": p.year,
            "cluster": p.cluster,
            "symbolSize": 20,
            "category": int(p.cluster) + 2,
            "label": {
                "show": True
            },
            "itemStyle": {
                "shadowColor": '#333333',
                "shadowBlur": 2,
                "shadowOffsetX": 2,
                "shadowOffsetY": 2
            }
        }]
        clusters = [p.cluster]
        edges = [];
        auths = [];
        kywds = []
        for author in p.authors:
            nodes.append({
                "id": author,
                "name": p.authors[author],
                "type": "Author",
                "category": 0,
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
                "category": 1,
                "symbolSize": 6
            })
            edges.append({
                "source": keyword,
                "target": p.n_id
            })
            kywds.append(keyword)
        for cit in cits_full:
            clusters.append(cit.cluster)
            nodes.append({
                "id": cit.n_id,
                "name": cit.paper_id,
                "type": "Paper",
                "title": cit.title,
                "year": cit.year,
                "cluster": cit.cluster,
                "symbolSize": 20,
                "category": int(cit.cluster) + 2,
                "label": {
                    "show": True
                }
            })
            edges.append({
                "source": cit.n_id,
                "target": p.n_id
            })
            for author in cit.authors:
                if author in auths:
                    edges.append({
                        "source": author,
                        "target": cit.n_id
                    })
            for keyword in cit.keywords:
                if keyword in kywds:
                    edges.append({
                        "source": keyword,
                        "target": cit.n_id
                    })
        clusters = sorted(list(set(clusters)))
        for node in nodes:
            if node['type'] == 'Paper':
                node['category'] = clusters.index(node['cluster']) + 2
        js = dict(type="force", categories=[], nodes=[], links=[])
        categories = [{'name': 'Author'}, {'name': 'Keyword'}]
        legends = ['Author', 'Keyword']
        for cluster in clusters:
            categories.append({'name': 'Clu-' + str(cluster)})
            legends.append('Clu-' + str(cluster))
        js['categories'] = categories
        js['nodes'] = nodes
        js['links'] = edges
        js['legends'] = legends
    elif load_type == 'W':
        year = request.form["year"]
        rs = n.cypher("MATCH (p1:Paper)-[r:reference]->(p2:Paper) WHERE p1.year={} AND p2.year={} RETURN r".format(year,year)).data()
        nodes = []; edges = []; categories = []; legends = []
        paper_nodes = []
        for rd in rs:
            r = rd['r']
            paper_nodes.append(r.start_node)
            paper_nodes.append(r.end_node)
            edges.append({"source": r.start_node['id'], "target": r.end_node['id']})
        node_ids = []; clusters = []
        for paper in paper_nodes:
            if paper['id'] in node_ids:
                pass
            else:
                nodes.append({
                    "id": paper['id'],
                    "name": paper['name'],
                    "type": "Paper",
                    "title": paper["title"],
                    "year": paper["year"],
                    "cluster": paper["cluster"],
                    "symbolize": 15,
                    "category": int(paper["cluster"]),
                    "label":{
                        "show": False
                    }
                })
                node_ids.append(paper['id'])
                clusters.append(paper["cluster"])
        clusters = sorted(list(set(clusters)))
        for cluster in clusters:
            categories.append({'name': 'Clu-' + str(cluster)})
            legends.append('Clu-' + str(cluster))
        js = dict(type="force", categories=[], nodes=[], links=[])
        js['categories'] = categories
        js['nodes'] = nodes
        js['links'] = edges
        js['legends'] = legends
    elif load_type == 'C':
        cluster = request.form["cluster"]
        year = request.form["year"]
        rs = n.cypher("MATCH (p1:Paper)-[r:reference]->(p2:Paper) WHERE p1.cluster=\'{}\' AND p2.cluster=\'{}\' AND p1.year={} AND p2.year={} RETURN r".format(cluster,cluster,year,year)).data()
        nodes = []; edges = []
        paper_nodes = []
        for rd in rs:
            r = rd['r']
            paper_nodes.append(r.start_node)
            paper_nodes.append(r.end_node)
            edges.append({"source": r.start_node['id'], "target": r.end_node['id']})
        node_ids = []; kwd_count = {}; paper_count = 0
        for paper in paper_nodes:
            if paper['id'] in node_ids:
                pass
            else:
                p = pt.Paper(n_id=paper['id'])
                nodes.append({
                    "id": paper['id'],
                    "name": paper['name'],
                    "type": "Paper",
                    "title": paper["title"],
                    "year": paper["year"],
                    "cluster": paper["cluster"],
                    "symbolize": 30,
                    "category": 2,
                    "label":{
                        "show": True
                    }
                })
                p = n.getNeighbors(p)
                for author in p.authors:
                    edges.append({
                        "source": author,
                        "target": p.n_id
                    })
                    if author in node_ids: pass
                    else:
                        nodes.append({
                            "id": author,
                            "name": p.authors[author],
                            "type": "Author",
                            "category": 0,
                            "symbolSize": 10
                        })
                        node_ids.append(author)
                for keyword in p.keywords:
                    edges.append({
                        "source": keyword,
                        "target": p.n_id
                    })
                    if p.keywords[keyword] in kwd_count:
                        kwd_count[p.keywords[keyword]] += 1
                    else:
                        kwd_count[p.keywords[keyword]] = 1
                    if keyword in node_ids: pass
                    else:
                        nodes.append({
                            "id": keyword,
                            "name": p.keywords[keyword],
                            "type": "Keyword",
                            "category": 1,
                            "symbolSize": 10
                        })
                        node_ids.append(keyword)
                node_ids.append(paper['id'])
                paper_count += 1
        js = dict(type="force", categories=[{'name': 'Author'},{'name': 'Keyword'},{'name': 'Paper'}], nodes=[], links=[])
        js['nodes'] = nodes
        js['links'] = edges
        js['legends'] = ['Author','Keyword','Paper']
        wordcloud_data = []
        for kwds in sorted(kwd_count.items(), key=lambda x:x[1], reverse=True):
            kwd = kwds[0]
            wordcloud_data.append({
                "name": kwd,
                "value": kwd_count[kwd]
            })
        js['wordcloud_data'] = wordcloud_data
        js['paper_count'] = paper_count
        js['top_keywords'] = wordcloud_data[:3]
    return js


@app.route('/paper/list', methods=['POST'])
def paper_list():
    mode = request.form["mode"]
    query = request.form["query"]
    return render_template("resultlist.html",query=query,mode=mode)

@app.route('/paper/list', methods=['GET'])
def paper_list_default():
    query = ""
    return render_template("resultlist.html",query=query,mode="Paper")

@app.route('/cluster')
def cluster():
    return render_template("cluster.html")

@app.route('/search',methods=['POST'])
def search():
    mode = request.form["mode"]
    query = request.form["query"]
    page = request.form["page"]
    response = n.search(query, page, mode=mode)
    result = response["result"]
    if result is None:
        abort(404)
    res_list = []
    for paper in result:
        detail = n.getPaperBasic(paper['name'])
        authors = []
        if mode == "Paper":
            for author in detail.authors:
                authors.append(detail.authors[author])
            info = {'id': detail.paper_id,
                    'title': re.sub(query, '<span class=\"text-danger\">' + query + '</span>', str(detail.title), flags=re.IGNORECASE),
                    'year': detail.year, 'cluster': detail.cluster, 'cits': detail.cit_count, 'author': authors}
            res_list.append(info)
        elif mode == "Author":
            for author in detail.authors:
                authors.append(re.sub(query, '<span class=\"text-danger\">' + query + '</span>', str(detail.authors[author]), flags=re.IGNORECASE))
            info = {'id': detail.paper_id, 'title': detail.title, 'year': detail.year, 'cluster': detail.cluster,
                    'cits': detail.cit_count, 'author': authors}
            res_list.append(info)
    return {"result": res_list, "count": response["count"]}


if __name__ == '__main__':
    m = mysql.mysqlConnection()
    n = neo4j.neoConnection()
    app.run(host='0.0.0.0', port=6517, threaded=True)
