"""Tests for the configuration dataclasses."""

from ingestion_engine import APIConfig, MariaDBConfig


class TestAPIConfig:
    def test_defines_a_default_timeout(self):
        """Without one a stalled endpoint would hang the pipeline forever."""

        config = APIConfig("https://example.com", {}, {})

        assert config.connect_timeout > 0
        assert config.read_timeout > 0

    def test_timeouts_can_be_overridden(self):
        config = APIConfig(
            "https://example.com", {}, {}, connect_timeout=1.5, read_timeout=2.5
        )

        assert config.timeout == (1.5, 2.5)

    def test_stays_constructible_with_three_positional_arguments(self):
        """The timeout fields were added after the class was already in use."""

        config = APIConfig("https://example.com", {"k": "v"}, {"p": "1"})

        assert config.url == "https://example.com"
        assert config.headers == {"k": "v"}
        assert config.params == {"p": "1"}


class TestMariaDBConfig:
    def test_defaults_to_the_standard_mariadb_port(self):
        assert MariaDBConfig("h", "u", "p", "db").port == 3306

    def test_port_can_be_overridden(self):
        assert MariaDBConfig("h", "u", "p", "db", port=3307).port == 3307

    def test_stays_constructible_with_four_positional_arguments(self):
        """The port field was added after the class was already in use."""

        config = MariaDBConfig("host", "user", "password", "database")

        assert (config.host, config.user, config.password, config.database) == (
            "host",
            "user",
            "password",
            "database",
        )
