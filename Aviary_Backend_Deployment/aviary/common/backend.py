import os
import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

import requests

from aviary.common.constants import TIMEOUT


def get_aviary_backend():
    """
    Establishes a connection to the Aviary backed after establishing
    the information using environmental variables.
    If the MOCK environmental variable is set, then a mock backend is used.
    Otherwise, the BACKEND_HOSTNAME and BACKEND_TOKEN environmental variables
    are required.

    If the BACKEND_HOSTNAME is localhost:<port>:
       - No BACKEND_TOKEN is required
       - http is used instead of https

    Returns:
        backend: An instance of the Backend class.
    """
    mock_backend = os.getenv("MOCK", False)
    if mock_backend:
        backend = MockBackend()
        return backend

    aviary_url = os.getenv("AVIARY_URL")
    if aviary_url:
        backend_token = os.getenv("BACKEND_TOKEN")
        bearer = f"Bearer {backend_token}"
        if not aviary_url.endswith("/"):
            aviary_url += "/"
        print("Connecting to Aviary backend at: ", aviary_url)
        backend = AviaryBackend(aviary_url, bearer)

        return backend

    backend_hostname = os.getenv("BACKEND_HOSTNAME")
    assert backend_hostname, "BACKEND_HOSTNAME must be set"
    if mock_backend or backend_hostname.startswith("localhost"):
        backend_token = os.getenv("BACKEND_TOKEN", "")
        backend_protocol = os.getenv("BACKEND_PROTOCOL", "http")
    else:
        backend_token = os.getenv("BACKEND_TOKEN")
        backend_protocol = os.getenv("BACKEND_PROTOCOL", "https")

    assert backend_token is not None, "BACKEND_TOKEN must be set"

    backend_url = f"{backend_protocol}://{backend_hostname}/"
    bearer = f"Bearer {backend_token}" if backend_token is not None else ""

    print("Connecting to Aviary backend at: ", backend_url)
    backend = AviaryBackend(aviary_url, bearer)
    return backend


class Backend(ABC):
    """Abstract interface for talking to Aviary."""

    @abstractmethod
    def models(self) -> List[str]:
        pass

    @abstractmethod
    def metadata(self, llm: str) -> Dict[str, Dict[str, Any]]:
        pass

    @abstractmethod
    def completions(self, prompt: str, llm: str) -> Dict[str, Union[str, float, int]]:
        pass

    @abstractmethod
    def batch_completions(
        self, prompts: List[str], llm: str
    ) -> List[Dict[str, Union[str, float, int]]]:
        pass


class AviaryBackend(Backend):
    """Interface for talking to Aviary.
    Deliberately designed to be similar to OpenAI's
    Completions interface.

    https://platform.openai.com/docs/api-reference/completions?lang=python
    """

    def __init__(self, backend_url: str, bearer: str):
        assert "::param" not in backend_url, "backend_url not set correctly"
        assert "::param" not in bearer, "bearer not set correctly"

        self.backend_url = backend_url
        self.bearer = bearer
        self.header = {"Authorization": self.bearer}

    def models(self) -> List[str]:
        url = self.backend_url + "models"
        resp = requests.get(url, headers=self.header, timeout=120)
        try:
            result = resp.json()
        except requests.JSONDecodeError:
            warnings.warn(
                f"Error decoding JSON from {url}. Text response: {resp.text}",
                stacklevel=2,
            )
            raise
        return result

    def metadata(self, llm: str) -> Dict[str, Dict[str, Any]]:
        url = self.backend_url + "metadata/" + llm.replace("/", "--")
        resp = requests.get(url, headers=self.header, timeout=120)
        try:
            result = resp.json()
        except requests.JSONDecodeError:
            warnings.warn(
                f"Error decoding JSON from {url}. Text response: {resp.text}",
                stacklevel=2,
            )
            raise
        return result

    def completions(self, prompt: str, llm: str) -> Dict[str, Union[str, float, int]]:
        url = self.backend_url + "query/" + llm.replace("/", "--")
        response = requests.post(
            url,
            headers=self.header,
            json={"prompt": prompt},
            timeout=TIMEOUT,
        )
        try:
            return response.json()[llm]
        except requests.JSONDecodeError:
            warnings.warn(
                f"Error decoding JSON from {url}. Text response: {response.text}",
                stacklevel=2,
            )
            raise

    def batch_completions(
        self, prompts: List[str], llm: str
    ) -> List[Dict[str, Union[str, float, int]]]:
        url = self.backend_url + "query/batch/" + llm.replace("/", "--")
        response = requests.post(
            url,
            headers=self.header,
            json=[{"prompt": prompt} for prompt in prompts],
            timeout=TIMEOUT,
        )
        try:
            return response.json()[llm]
        except requests.JSONDecodeError:
            warnings.warn(
                f"Error decoding JSON from {url}. Text response: {response.text}",
                stacklevel=2,
            )
            raise


class MockBackend(Backend):
    """Mock backend for testing"""

    def __init__(self):
        pass

    def models(self) -> List[str]:
        return ["A", "B", "C"]

    def metadata(self, llm: str) -> Dict[str, Dict[str, Any]]:
        return {
            "metadata": {
                "model_config": {
                    "model_id": llm,
                    "model_url": f"https://huggingface.co/org/{llm}",
                    "model_description": f"This is a model description for model {llm}",
                }
            }
        }

    def completions(self, prompt: str, llm: str) -> Dict[str, Union[str, float, int]]:
        return {
            "generated_text": prompt,
            "total_time": 99,
            "num_total_tokens": 42.3,
        }

    def batch_completions(
        self, prompts: List[str], llm: str
    ) -> List[Dict[str, Union[str, float, int]]]:
        return [
            {
                "generated_text": prompt,
                "total_time": 99,
                "num_total_tokens": 42.3,
            }
            for prompt in prompts
        ]
