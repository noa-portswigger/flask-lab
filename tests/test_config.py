# SPDX-License-Identifier: MIT
# Copyright (c) 2025 flask-lab contributors

import tempfile
from pathlib import Path
import pytest
from flask_lab.config import load_config, Config, SqliteConfig, RdsConfig, DatabaseConfig


def test_load_config_missing_file():
    """Test that load_config raises FileNotFoundError when config file doesn't exist"""
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config('/nonexistent/config.toml')


def test_load_config_sqlite_default():
    """Test loading a minimal SQLite configuration"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[database]
type = "sqlite"

[database.sqlite]
uri = "sqlite:////tmp/test.db"
""")
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config is not None
        assert isinstance(config, Config)
        assert config.database.type == 'sqlite'
        assert config.database.sqlite.uri == 'sqlite:////tmp/test.db'
    finally:
        Path(config_path).unlink()


def test_load_config_rds_with_iam():
    """Test loading RDS configuration"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[database]
type = "rds"

[database.rds]
host = "test.rds.amazonaws.com"
port = 5432
name = "testdb"
user = "testuser"
region = "us-west-2"
""")
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config is not None
        assert config.database.type == 'rds'
        assert config.database.rds.host == 'test.rds.amazonaws.com'
        assert config.database.rds.port == 5432
        assert config.database.rds.name == 'testdb'
        assert config.database.rds.user == 'testuser'
        assert config.database.rds.region == 'us-west-2'
        assert config.database.rds.hostname_override is None
    finally:
        Path(config_path).unlink()


def test_load_config_rds_with_hostname_override():
    """Test loading RDS configuration with hostname override"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[database]
type = "rds"

[database.rds]
host = "test.rds.amazonaws.com"
port = 5432
name = "testdb"
user = "testuser"
region = "eu-west-1"
hostname_override = "localhost"
""")
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config is not None
        assert config.database.rds.host == 'test.rds.amazonaws.com'
        assert config.database.rds.hostname_override == 'localhost'
    finally:
        Path(config_path).unlink()


def test_load_config_rds_defaults():
    """Test that RDS config uses default values for optional fields"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[database]
type = "rds"

[database.rds]
host = "test.rds.amazonaws.com"
port = 5432
name = "testdb"
user = "testuser"
region = "us-east-1"
""")
        config_path = f.name

    try:
        config = load_config(config_path)

        assert config is not None
        assert config.database.rds.port == 5432
        assert config.database.rds.region == 'us-east-1'
        assert config.database.rds.hostname_override is None  # optional default
    finally:
        Path(config_path).unlink()


def test_config_dataclass_types():
    """Test that config objects have correct types"""
    sqlite_config = SqliteConfig()
    rds_config = RdsConfig(
        host='test.com',
        port=5432,
        name='testdb',
        user='testuser',
        region='us-east-1'
    )
    db_config = DatabaseConfig(type='sqlite', sqlite=sqlite_config, rds=rds_config)
    config = Config(database=db_config)
    assert isinstance(config.database.sqlite, SqliteConfig)
    assert isinstance(config.database.rds, RdsConfig)
    assert config.database.type == 'sqlite'


def test_load_config_invalid_type():
    """Test that load_config raises error for invalid database type"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[database]
type = "mysql"
""")
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="Invalid database type: 'mysql'"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()


def test_load_config_missing_type():
    """Test that load_config raises error when type is missing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[database]
""")
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="Invalid database type: 'None'"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()


def test_load_config_rds_missing_required_fields():
    """Test that load_config raises error when RDS required fields are missing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[database]
type = "rds"

[database.rds]
host = "test.rds.amazonaws.com"
""")
        config_path = f.name

    try:
        with pytest.raises(ValueError, match="Missing required RDS configuration fields: port, name, user, region"):
            load_config(config_path)
    finally:
        Path(config_path).unlink()