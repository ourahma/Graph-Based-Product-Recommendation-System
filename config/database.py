from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv(override=True)


class Neo4jClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.driver = GraphDatabase.driver(
                os.getenv("NEO4J_URI"),
                auth=(
                    os.getenv("NEO4J_USER"),
                    os.getenv("NEO4J_PASSWORD"),
                ),
            )
            cls._instance.database = os.getenv("NEO4J_DATABASE")
        return cls._instance

    def query(self, cypher: str, params: dict = {}) -> list[dict]:
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params)
            return [record.data() for record in result]

    def run(self, cypher: str, params: dict = {}) -> None:
        with self.driver.session(database=self.database) as session:
            session.run(cypher, params)

    def close(self):
        self.driver.close()


# Singleton exporté
db = Neo4jClient()