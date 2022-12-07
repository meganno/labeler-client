from labeler_ui import Dashboard
from labeler_client.helpers import get_request


class Statistic:

    def __init__(self, service) -> None:
        self.__service = service

    def show(self, config={}):
        service_varname = self.__service.get_variable_name(
            target=self.__service)
        widget = Dashboard(service=service_varname, config=config)
        return widget.show()

    def get_label_progress(self):
        payload = self.__service.get_base_payload()
        path = self.__service.get_service_endpoint('get_label_progress')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_label_distributions(self, label_name: str = None):
        if label_name is None or len(label_name) == 0:
            raise Exception("label_name can not be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update({'label_name': label_name})
        path = self.__service.get_service_endpoint('get_label_distribution')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_annotator_contributions(self):
        payload = self.__service.get_base_payload()
        path = self.__service.get_service_endpoint(
            'get_annotator_contribution')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_annotator_agreements(self, label_name: str = None):
        if label_name is None or len(label_name) == 0:
            raise Exception("label_name can not be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update({'label_name': label_name})
        path = self.__service.get_service_endpoint('get_annotator_agreement')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_embeddings(self, label_name: str = None, embed_type: str = None):
        if label_name is None or len(label_name) == 0:
            raise Exception("'label_name' can not be None or empty.")
        elif embed_type is None or len(embed_type) == 0:
            raise Exception("'embed_type' can not be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update({'label_name': label_name})
        path = self.__service.get_service_endpoint('get_embeddings').format(
            embed_type=embed_type)
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)