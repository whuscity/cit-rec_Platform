from py2neo import Graph, Node, Relationship, NodeMatcher, RelationshipMatcher
from instance import paper,author


class neoConnection:
    def __init__(self):
        self.graph = Graph(
            "http://localhost:7474",
            user = "cradmin",
            password = "888888"
        )

    def getPaperBasic(self,paperid):
        n_matcher = NodeMatcher(self.graph)
        r_matcher = RelationshipMatcher(self.graph)
        p = paper.Paper()
        paper_node = n_matcher.match("Paper",name=str(paperid)).first()
        print(paper_node)
        if paper_node is None: return p
        p.n_id = paper_node['id']
        p.paper_id = paper_node['name']
        p.title = paper_node['title']
        p.year = paper_node['year']
        p.abstract = paper_node['abstract']
        p.database = paper_node['dbname']
        p.cluster = paper_node['cluster']
        authors = r_matcher.match((None, paper_node), r_type="author").all()
        for author in authors:
            p.authors[author.start_node['id']] = author.start_node['name']
        return p


    def getNeighbors(self,paper):
        n_matcher = NodeMatcher(self.graph)
        r_matcher = RelationshipMatcher(self.graph)
        paper_node = n_matcher.match("Paper",id=paper.n_id).first()
        paper.paper_id = paper_node['name']
        paper.title = paper_node['title']
        paper.year = paper_node['year']
        paper.abstract = paper_node['abstract']
        paper.database = paper_node['dbname']
        paper.cluster = paper_node['cluster']
        authors = r_matcher.match((None,paper_node),r_type="author").all()
        keywords = r_matcher.match((None, paper_node), r_type="keyword").all()
        for author in authors:
            paper.authors[author.start_node['id']] = author.start_node['name']
        for keyword in keywords:
            paper.keywords[keyword.start_node['id']] = keyword.start_node['name']
        refs = r_matcher.match((None,paper_node),r_type="reference").all()
        for ref in refs:
            paper.refs[ref.start_node['id']] = ref.start_node['name']
        cits = r_matcher.match((paper_node, None), r_type="reference").all()
        for cit in cits:
            paper.cits[cit.end_node['id']] = cit.end_node['name']
        recs = r_matcher.match((paper_node, None), r_type="recommend").all()
        for rec in recs:
            paper.recs[rec.end_node['id']] = rec.end_node['name']
            paper.rec_sim[rec.end_node['id']] = rec['sim']
        return paper

    def getAuthorInfo(self,author_id):
        n_matcher = NodeMatcher(self.graph)
        r_matcher = RelationshipMatcher(self.graph)
        author_node = n_matcher.match("Author",id=author_id).first()
        a = author.Author()
        a.n_id = author_id
        a.name = author_node['name']
        a.database = 'aan'
        a.paper_count_year = eval(author_node['year'])
        a.paper_count_cluster = eval(author_node['cluster'])
        a.paper_count_keyword = eval(author_node['keywords'])
        a.co_authors = eval(author_node['co_auths'])
        a_ps = r_matcher.match((author_node,None),r_type="author")
        for a_p in a_ps:
            # print(a_p.end_node['id'])
            a.papers.append(self.getNeighbors(paper.Paper(n_id=a_p.end_node['id'])))
        a.paper_count = len(a.papers)
        a.cluster_count = len(a.paper_count_cluster)
        a.co_authors_count = len(a.co_authors)
        a.papers.sort(key=lambda paper: paper.year)
        a.co_authors = dict(sorted(a.co_authors.items(), key=lambda x: x[1], reverse=True))
        a.paper_count_keyword = dict(sorted(a.paper_count_keyword.items(), key=lambda x: x[1], reverse=True))
        a.paper_count_cluster = dict(sorted(a.paper_count_cluster.items(), key=lambda x: x[1], reverse=True))
        a.paper_count_year = dict(sorted(a.paper_count_year.items()))
        return a

    def getAuthorBasic(self,author_id):
        n_matcher = NodeMatcher(self.graph)
        author_node = n_matcher.match("Author",id=author_id).first()
        a = author.Author()
        a.n_id = author_id
        a.name = author_node['name']
        a.database = 'aan'
        a.paper_count = author_node['paper_count']
        a.co_authors_count = len(eval(author_node['co_auths']).keys())
        a.cluster_count = len(eval(author_node['cluster']).keys())
        return a

    def getKeyword(self,keyword_id):
        n_matcher = NodeMatcher(self.graph)
        keyword_node = n_matcher.match("Keyword", id=keyword_id).first()
        return keyword_node['name'] if keyword_node else 'NULL'