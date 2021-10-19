import pymysql
from instance import paper


class mysqlConnection:
    def __init__(self):
        self.connection = pymysql.connect(
            host="localhost",
            user="cradmin",
            passwd="888888",
            database="cit_rec"
        )
        self.cursor = self.connection.cursor()

    def close(self):
        self.cursor.close()
        self.connection.close()

    def getPaperInfo(self, paperids):
        if len(paperids) == 0: return []
        sql = """SELECT id, title, year, abstract, content, dbname, n_id, cluster
                 FROM paper_info
                 INNER JOIN
                 (
                 SELECT id AS n_id ,node_name
                 FROM node_id
                 WHERE node_name IN (""" + str(paperids).replace('[', '').replace(']', '') + """)
                 ) AS node ON paper_info.id = node.node_name"""
        print(sql)
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        papers = []
        for row in data:
            p = paper.Paper()
            p.paper_id = row[0]
            p.n_id = row[6]
            p.title = row[1]
            p.year = row[2]
            p.abstract = row[3]
            p.database = row[5]
            p.cluster = row[7]
            papers.append(p)
        return papers
