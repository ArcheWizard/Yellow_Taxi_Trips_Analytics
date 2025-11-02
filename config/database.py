"""
Database configuration module for City Rides Analytics.

This module provides database connection configuration and management
using environment variables loaded from .env file.
"""

import os

import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()


class DatabaseConfig:
    """Database configuration class for PostgreSQL connection."""

    def __init__(self):
        """Initialize database configuration from environment variables."""
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.database = os.getenv("DB_NAME", "city_rides_db")
        self.user = os.getenv("DB_USER", "rides_user")
        self.password = os.getenv("DB_PASSWORD", "")

    def get_connection_string(self):
        """
        Get PostgreSQL connection string.

        Returns:
            str: PostgreSQL connection string in format:
                postgresql://user:password@host:port/database
        """
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    def get_engine(self):
        """
        Create and return SQLAlchemy engine.

        Returns:
            Engine: SQLAlchemy engine instance
        """
        return create_engine(self.get_connection_string())

    def get_session(self):
        """
        Create and return SQLAlchemy session.

        Returns:
            Session: SQLAlchemy session instance
        """
        engine = self.get_engine()
        Session = sessionmaker(bind=engine)
        return Session()

    def get_connection(self):
        """
        Create and return psycopg2 connection.

        Returns:
            connection: psycopg2 connection instance
        """
        return psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
        )


if __name__ == "__main__":
    # Test configuration
    config = DatabaseConfig()
    print(f"Database: {config.database}")
    print(f"Host: {config.host}")
    print(f"Port: {config.port}")
    print(f"User: {config.user}")
    print("Connection string generated successfully!")
