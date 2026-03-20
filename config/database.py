from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv
import os
import atexit
from typing import Any

load_dotenv(override=True)


class Neo4jClient:
    _instance = None
    driver: Driver | None = None
    database: str | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            
            uri = os.getenv("NEO4J_URI")
            user = os.getenv("NEO4J_USER")
            password = os.getenv("NEO4J_PASSWORD")
            database = os.getenv("NEO4J_DATABASE", "neo4j")

            if not uri or not user or not password:
                raise ValueError("Missing required Neo4j environment variables")

            cls._instance.driver = GraphDatabase.driver(
                uri,
                auth=(user, password),
            )
            cls._instance.database = database
            
            atexit.register(cls._instance.close)
            
        return cls._instance

    def query(self, cypher: str, params: dict[str, Any] | None = None) -> list[dict]:
        if params is None:
            params = {}
        
        if self.driver is None:
            raise RuntimeError("Driver not initialized")
            
        with self.driver.session(database=self.database) as session:
            result = session.run(cypher, params)  # type: ignore
            return [record.data() for record in result]

    def run(self, cypher: str, params: dict[str, Any] | None = None) -> None:
        if params is None:
            params = {}
        
        if self.driver is None:
            raise RuntimeError("Driver not initialized")
            
        with self.driver.session(database=self.database) as session:
            session.run(cypher, params).consume()  # type: ignore

    def close(self):
        if self.driver:
            self.driver.close()


db = Neo4jClient()