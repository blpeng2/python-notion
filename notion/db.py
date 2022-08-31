import requests
from notion import database
from notion.response import Response


class Database:
    def __init__(self, url, api, **attributes) -> None:
        """
        url: 데이터베이스가 존재하는 http 주소입니다.
        api: notionAPI key 입니다.
        attr: Attribute 클래스 인스턴스들의 딕셔너리 묶음입니다.
        """
        self.headers22 = {
            "Accept": "application/json",
            "Notion-Version": "2022-06-28",
            "Authorization": f"Bearer {api}"
        }

        self.headers21 = {
            "Accept": "application/json",
            "Notion-Version": "2021-08-16",
            "Content-Type": "application/json",
            "Authorization": f"{api}"
        }

        response = requests.get(
            "https://api.notion.com/v1/databases/" +
            url.split("/")[-1].split("?")[0],
            headers=self.headers22
        ).json()
        # attributes와 properties를 구분할 방안이 필요함.
        self.id = response["id"]
        self.title = response["title"]
        self.properties = response["properties"]
        self.api = api
        self.attributes = attributes
        self.primaryKey: str = None
        self.foreignDB: Database = None

        # FIXME: multi_select타입인 경우도 넣어야함
        for key, field in attributes.items():
            if self.properties[key]["type"] == "title":
                field.set_type("title")
                if field.pk:
                    if self.primaryKey:
                        raise Exception("primaryKey가 중복되었습니다.")
                    self.primaryKey = key
                if field.foreign:
                    self.foreignDB = field.foreign
            elif self.properties[key]["type"] == "rich_text":
                field.set_type("rich_text")
                if field.pk:
                    if self.primaryKey:
                        raise Exception("primaryKey가 중복되었습니다.")
                    self.primaryKey = key
                if field.foreign:
                    self.foreignDB = field.foreign
            else:
                raise Exception("유효하지 않는 타입입니다.")

    def checkType(self, field, content):
        match field.__class__:
            case database.IntField:
                try:
                    int(content)
                except ValueError:
                    raise Exception(f"{content}는 int타입이 아닙니다.")
                else:
                    return
            case database.CharField:
                return
            case database.FloatField:
                try:
                    float(content)
                except ValueError:
                    raise Exception(f"{content}는 float타입이 아닙니다.")
                else:
                    return

    # 타입이 title, rich_text에 따라서 content 반환하는 함수
    def getProperty(self, isTitle, content):
        if isTitle:
            return {
                "title": [{
                    "text": {
                        "content": str(content)
                    }
                }]
            }
        else:
            return {
                "rich_text": [{
                    "text": {
                        "content": str(content)
                    }
                }]
            }

    def insert(self, **contents):
        if self.foreignDB:
            url = f"https://api.notion.com/v1/databases/{self.foreignDB.id}/query"
            payload = {"page_size": 100}
            # TODO res가 error가 나온경우 예외처리 해야함
            res = requests.post(url, json=payload, headers=self.headers21).json()

            foreign = None

            for result in res["results"]:
                if result["properties"][self.foreignDB.primaryKey]["title"][0]["plain_text"] == str(contents[self.foreignDB.primaryKey]):
                    foreign = True
            if not foreign:
                raise Exception("Foreign Error")
        url = "https://api.notion.com/v1/pages"
        properties = {}
        # attributeValue는 Field class입니다.
        for attributeKey, attributeValue in self.attributes.items():
            isTitle = True if attributeValue.type == "title" else False
            self.checkType(attributeValue, contents[attributeKey])
            properties[attributeKey] = self.getProperty(
                isTitle, contents[attributeKey]
            )

        payload = {
            "parent": {
                "type": "database_id",
                "database_id": f"{self.id}"
            },
            "properties": properties
        }
        if requests.post(url, json=payload, headers=self.headers22):
            return True
        return False


    def read(self) -> tuple:
        url = f"https://api.notion.com/v1/databases/{self.id}/query"
        payload = {"page_size": 100}
        res = Response(url, payload, self.headers21)
        return res.getProperties()


    def update(self, key, before_content, **after_content) -> bool:

        for result in self.read():
            if result["property"][key]["content"] == before_content:
                url = f"https://api.notion.com/v1/pages/{result['id']}"
                properties = {}

                for contentKey, contentValue in after_content.items():
                    if result["property"][contentKey]["type"] == "title":
                        properties[contentKey] = {
                            "title": [{"text": {"content": str(contentValue)}}]}
                    elif result["property"][contentKey]["type"] == "rich_text":
                        properties[contentKey] = {
                            "rich_text": [{"text": {"content": str(contentValue)}}]}
                payload = {
                    "parent": {
                        "type": "database_id",
                        "database_id": f"{self.id}"
                    },
                    "properties": properties
                }
                response = requests.patch(url, json=payload, headers=self.headers22).json()
                if response["object"] == "error":
                    raise Exception(response["message"])
                else:
                    return True
            else:
                raise Exception(f"{key} = {before_content}의 요소를 찾지 못했습니다.")

    def delete(self, key, content) -> bool:
        for result in self.read():
            # key를 잘못 입력한 경우 예외처리 해야함
            if result["property"][key]["content"] == content:
                url = f"https://api.notion.com/v1/pages/{result['id']}"
                payload = {"archived": True}
                response = requests.patch(url, json=payload, headers=self.headers22).json()
                if response["object"] == "error":
                    raise Exception(response["message"])
                else:
                    return True
            else:
                raise Exception(f"{key} = {content}의 요소를 찾지 못했습니다.")
