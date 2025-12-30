# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

from flask_lab.db import build_uri
from flask_lab.config import Config, DatabaseConfig, SqliteConfig, RdsConfig


def test_build_uri_basic():
    """Test building basic RDS URI"""
    rds_config = RdsConfig(
        host='test.rds.amazonaws.com',
        port=5432,
        name='testdb',
        user='testuser',
        region='us-west-2'
    )
    db_config = DatabaseConfig(type='rds', rds=rds_config, sqlite=SqliteConfig())
    config = Config(database=db_config)

    uri = build_uri(config)

    expected = 'postgresql://testuser@test.rds.amazonaws.com:5432/testdb'
    assert uri == expected


def test_build_uri_with_hostname_override():
    """Test building RDS URI with hostname override"""
    rds_config = RdsConfig(
        host='test.rds.amazonaws.com',
        port=5432,
        name='testdb',
        user='testuser',
        region='us-west-2',
        hostname_override='localhost'
    )
    db_config = DatabaseConfig(type='rds', rds=rds_config, sqlite=SqliteConfig())
    config = Config(database=db_config)

    uri = build_uri(config)

    # URI should use hostname_override for connection
    expected = 'postgresql://testuser@localhost:5432/testdb'
    assert uri == expected


def test_build_uri_with_custom_port():
    """Test building RDS URI with custom port"""
    rds_config = RdsConfig(
        host='test.rds.amazonaws.com',
        port=3306,
        name='testdb',
        user='testuser',
        region='us-east-1'
    )
    db_config = DatabaseConfig(type='rds', rds=rds_config, sqlite=SqliteConfig())
    config = Config(database=db_config)

    uri = build_uri(config)

    expected = 'postgresql://testuser@test.rds.amazonaws.com:3306/testdb'
    assert uri == expected


def test_build_uri_different_regions():
    """Test building RDS URI for different regions"""
    for region in ['us-east-1', 'eu-west-1', 'ap-southeast-1']:
        rds_config = RdsConfig(
            host=f'test.{region}.rds.amazonaws.com',
            port=5432,
            name='testdb',
            user='testuser',
            region=region
        )
        db_config = DatabaseConfig(type='rds', rds=rds_config, sqlite=SqliteConfig())
        config = Config(database=db_config)

        uri = build_uri(config)

        expected = f'postgresql://testuser@test.{region}.rds.amazonaws.com:5432/testdb'
        assert uri == expected
