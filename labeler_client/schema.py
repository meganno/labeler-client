from labeler_client.helpers import get_request, post_request


class Schema:

    def __init__(self, service):
        self.__service = service

    def value(self, active=None):
        payload = self.__service.get_base_payload()
        payload['active'] = active
        path = self.__service.get_service_endpoint('get_schemas')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_active_schemas(self):
        return self.value(active=True)

    def get_history(self):
        return self.value(active=False)

    def set_schemas(self, schemas=None):
        payload = self.__service.get_base_payload()
        payload['schemas'] = schemas
        path = self.__service.get_service_endpoint('set_schemas')
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)