import requests


class Client:
    def __init__(self, api_key) -> None:
        self.api_key = api_key
        self.database = None
        self.page = None
        self.block = None

    def set_database(self, database_id):
        self.database = self.Database(self.api_key, database_id)
        return True

    def set_page(self, page_id):
        self.page = self.Page(self.api_key, page_id)
        return True

    def set_block(self, block_id):
        self.block = self.Block(self.api_key, block_id)
        return True

    class Database:
        def __init__(self, api_key, database_id) -> None:
            self.api_key = api_key
            self.database_id = database_id

        def get_elements_text(self, attribute: str) -> list:
            url = f"https://api.notion.com/v1/databases/{self.database_id}/query"

            payload = {"page_size": 100}
            headers = {
                "Accept": "application/json",
                "Notion-Version": "2021-08-16",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.post(url, json=payload, headers=headers)
            arr = []
            for result in response.json()["results"]:
                arr.append(result["properties"]
                           [f"{attribute}"]["title"][0]["plain_text"])
            return arr

        def remove_elements_text(self, attribute: str, text: str):
            url = f"https://api.notion.com/v1/databases/{self.database_id}/query"
            payload = {"page_size": 100}
            headers = {
                "Accept": "application/json",
                "Notion-Version": "2021-08-16",
                "Content-Type": "application/json",
                "Authorization": f"{self.api_key}"
            }
            response = requests.post(url, json=payload, headers=headers)

            for result in response.json()["results"]:
                if result["properties"][f"{attribute}"]["title"][0]["plain_text"] == text:
                    page_id = result["url"].split("/")[-1].split("-")[-1]
                    url = f"https://api.notion.com/v1/pages/{page_id}"
                    payload = {"archived": True}
                    headers = {
                        "Accept": "application/json",
                        "Notion-Version": "2022-06-28",
                        "Content-Type": "application/json",
                        "Authorization": f"{self.api_key}"
                    }
                    response = requests.patch(
                        url, json=payload, headers=headers)

        def add_element(self, attributes, contents):
            url = "https://api.notion.com/v1/pages"

            properties = {}

            properties[attributes[0]] = {
                "title": [{"text": {"content": contents[0]}}]
            }

            for i in range(1, len(attributes)):
                properties[attributes[i]] = {"rich_text": [{"text": {"content": contents[i]}}]}

            payload = {
                "parent": {
                    "type": "database_id",
                    "database_id": f"{self.database_id}"
                },
                "properties": properties
            }
            headers = {
                "Accept": "application/json",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
                "Authorization": f"{self.api_key}"
            }

            response = requests.post(url, json=payload, headers=headers)

            print(response.text)

    class Page:
        def __init__(self, api_key, page_id) -> None:
            self.api_key = api_key
            self.page_id = page_id

        def get_page(self) -> dict:
            url = f"https://api.notion.com/v1/pages/{self.page_id}"
            headers = {
                "Accept": "application/json",
                "Notion-Version": "2022-06-28",
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.get(url, headers=headers)
            return response.json()

    class Block:
        def __init__(self, api_key, block_id) -> None:
            self.api_key = api_key
            self.block_id = block_id

        def get_block(self) -> dict:
            url = f"https://api.notion.com/v1/blocks/{self.block_id}"

            headers = {
                "Accept": "application/json",
                "Notion-Version": "2022-06-28",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.get(url, headers=headers)

            return response.json()

        def get_children_blocks(self, mode) -> list:
            url = f"https://api.notion.com/v1/blocks/{self.block_id}/children?page_size=100"

            headers = {
                "Accept": "application/json",
                "Notion-Version": "2022-06-28",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.get(url, headers=headers)
            arr = []
            if mode == "json":
                for result in response.json()["results"]:
                    arr.append(result)
            elif mode == "text":
                for result in response.json()["results"]:
                    arr.append(result["paragraph"]["rich_text"][0]["text"]
                               ["content"] if result["paragraph"]["rich_text"] else None)
            return arr

        def get_children_block(self, idx: int, mode) -> str:
            url = f"https://api.notion.com/v1/blocks/{self.block_id}/children?page_size=100"

            headers = {
                "Accept": "application/json",
                "Notion-Version": "2022-06-28",
                "Authorization": f"Bearer {self.api_key}"
            }
            response = requests.get(url, headers=headers)
            if mode == "json":
                return response.json()["results"][idx]
            elif mode == "text":
                return response.json()["results"][idx]["paragraph"]["rich_text"][0]["text"]["content"] if response.json()["results"][idx]["paragraph"]["rich_text"] else None

        def delete(self):
            url = f"https://api.notion.com/v1/blocks/{self.block_id}"

            headers = {
                "Accept": "application/json",
                "Notion-Version": "2022-06-28",
                "Authorization": f"Bearer {self.api_key}"
            }

            response = requests.delete(url, headers=headers)
            if response.json()["object"] == "block":
                return response.json()
            elif response.json()["object"] == "error":
                return response.json()["message"]

        def append_children_block(self):
            url = f"https://api.notion.com/v1/blocks/{self.block_id}/children"

            headers = {
                "Accept": "application/json",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "object": "block",
                "type": "heading_1",
                "archived": False,
                "has_children": False,
                # ...other keys excluded
                "heading_1": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Lacinato kale",
                                "link": None
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "green"
                            },
                            "plain_text": "Lacinato kale",
                            "href": None
                        }
                    ],
                    "color": "default"
                }
            }

            response = requests.patch(url, json=payload, headers=headers)

            print(response.text)
