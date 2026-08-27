from pathlib import Path

import requests


class IpfsService:
    def __init__(self, api_url: str, timeout: int = 30, origin: str = 'http://localhost:5173'):
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.origin = origin

    def add_file(self, file_path: Path) -> str:
        with file_path.open('rb') as image_file:
            response = requests.post(
                f'{self.api_url}/add',
                files={'file': (file_path.name, image_file)},
                headers={'Origin': self.origin},
                timeout=self.timeout,
            )
        response.raise_for_status()
        return response.json()['Hash']

    def gateway_url(self, cid: str) -> str:
        return f'ipfs://{cid}'

    def read_file(self, cid: str) -> bytes:
        response = requests.post(
            f'{self.api_url}/cat',
            params={'arg': cid},
            headers={'Origin': self.origin},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.content
