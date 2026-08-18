"""Tests for APIConnector, including how it maps HTTP failures."""

import re

import pytest
import requests

from ingestion_engine import APIConfig, APIConnector

URL = "https://example.com/records"
PAYLOAD = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]


class FakeResponse:
    status_code = 200

    def __init__(self, payload=None, error: Exception | None = None):
        self._payload = PAYLOAD if payload is None else payload
        self._error = error

    def raise_for_status(self) -> None:
        if self._error is not None:
            raise self._error

    def json(self):
        return self._payload


@pytest.fixture
def spy_get(monkeypatch: pytest.MonkeyPatch):
    """Replace requests.get with a spy recording how it was called."""

    calls: list[dict] = []

    def install(response=None, error: Exception | None = None):
        def fake_get(url, **kwargs):
            calls.append({"url": url, **kwargs})

            if error is not None:
                raise error

            return FakeResponse() if response is None else response

        monkeypatch.setattr(requests, "get", fake_get)

        return calls

    return install


def extract(config: APIConfig, table) -> list[dict]:
    return list(APIConnector(config).extract(table))


def build_config(**overrides) -> APIConfig:
    settings = {"url": URL, "headers": {}, "params": {}}
    settings.update(overrides)

    return APIConfig(**settings)


class TestRequest:
    def test_the_configured_url_headers_and_params_are_sent(self, spy_get, table):
        calls = spy_get()
        config = build_config(headers={"Authorization": "token"}, params={"page": "1"})

        extract(config, table)

        assert calls[0]["url"] == URL
        assert calls[0]["headers"] == {"Authorization": "token"}
        assert calls[0]["params"] == {"page": "1"}

    def test_a_timeout_is_always_sent(self, spy_get, table):
        """Without one a stalled endpoint hangs the pipeline forever."""

        calls = spy_get()

        extract(build_config(), table)

        assert calls[0]["timeout"] is not None

    def test_the_configured_timeout_is_the_one_sent(self, spy_get, table):
        calls = spy_get()
        config = build_config(connect_timeout=1.5, read_timeout=2.5)

        extract(config, table)

        assert calls[0]["timeout"] == (1.5, 2.5)

    def test_nothing_is_requested_until_the_records_are_consumed(self, spy_get, table):
        """Extraction is a generator, so the pipeline controls when it starts."""

        calls = spy_get()

        records = APIConnector(build_config()).extract(table)

        assert calls == []

        next(records)

        assert len(calls) == 1


class TestRecords:
    def test_every_record_of_the_response_is_yielded(self, spy_get, table):
        spy_get()

        assert extract(build_config(), table) == PAYLOAD

    def test_an_empty_response_yields_nothing(self, spy_get, table):
        spy_get(response=FakeResponse(payload=[]))

        assert extract(build_config(), table) == []


class TestFailures:
    def test_a_malformed_url_is_reported_as_such(self, spy_get, table):
        spy_get(error=requests.exceptions.MissingSchema("no scheme"))

        with pytest.raises(requests.exceptions.MissingSchema):
            extract(build_config(url="example.com"), table)

    def test_a_timeout_stays_a_timeout(self, spy_get, table):
        """Callers must be able to tell a timeout from any other failure."""

        spy_get(error=requests.exceptions.ReadTimeout("too slow"))

        with pytest.raises(requests.exceptions.Timeout):
            extract(build_config(), table)

    def test_a_connect_timeout_is_also_reported_as_a_timeout(self, spy_get, table):
        """ConnectTimeout also inherits from ConnectionError, so order matters."""

        spy_get(error=requests.exceptions.ConnectTimeout("unreachable"))

        with pytest.raises(requests.exceptions.Timeout):
            extract(build_config(), table)

    def test_any_other_request_failure_becomes_a_runtime_error(self, spy_get, table):
        spy_get(error=requests.exceptions.ConnectionError("refused"))

        with pytest.raises(RuntimeError, match="Failed to retrieve data"):
            extract(build_config(), table)

    def test_the_original_failure_is_kept_as_the_cause(self, spy_get, table):
        original = requests.exceptions.ConnectionError("refused")
        spy_get(error=original)

        with pytest.raises(RuntimeError) as error:
            extract(build_config(), table)

        assert error.value.__cause__ is original

    def test_an_error_status_stops_the_extraction(self, spy_get, table):
        spy_get(response=FakeResponse(error=requests.exceptions.HTTPError("500")))

        with pytest.raises(RuntimeError, match="Failed to retrieve data"):
            extract(build_config(), table)

    def test_the_failing_url_is_named_in_the_error(self, spy_get, table):
        spy_get(error=requests.exceptions.ConnectionError("refused"))

        with pytest.raises(RuntimeError, match=re.escape(URL)):
            extract(build_config(), table)
