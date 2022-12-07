from labeler_ui import Annotation
from labeler_client.helpers import get_request
import json


class Subset():

    def __init__(self, service, data_uuids=[], meta_names: list = []):
        self.__data_uuids = data_uuids
        self.__service = service
        self.__annotation_list = None
        self.__meta_names = meta_names

    def get_uuid_list(self):
        return self.__data_uuids

    def value(self):
        if self.__annotation_list is None:
            self.get_annotation_list()
        return self.__annotation_list

    def get_data_by_uuid(self, uuid):
        for annotation in self.__annotation_list:
            if annotation['uuid'] == uuid:
                return annotation
        return None

    def get_annotation_list(self):
        payload = self.__service.get_base_payload()
        payload.update({
            'uuid_list': self.__data_uuids,
            'meta_names': self.__meta_names
        })
        path = self.__service.get_service_endpoint('get_annotations')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            self.__annotation_list = response.json()
            return self.__annotation_list
        else:
            raise Exception(response.text)

    def show(self, config={}):
        dataset_varname = self.__service.get_variable_name(target=self)
        service_varname = self.__service.get_variable_name(
            target=self.__service)
        widget = Annotation(subset=dataset_varname,
                            service=service_varname,
                            config=config)
        return widget.show()

    def set_annotations(self, uuid=None, labels=None):
        annotator_user_id = self.__service.get_annotator()['user_id']
        if uuid is None:
            raise Exception("UUID can not be None.")
        elif labels is None:
            raise Exception(
                f'Labels can not be None. For clearing annotations, use {{}}.')
        labels['annotator'] = annotator_user_id
        added = False
        index = -1
        for datapoint_idx, datapoint in enumerate(self.__annotation_list):
            if datapoint['uuid'] == uuid:
                index = datapoint_idx
                for annotation_idx, annotation in enumerate(
                        datapoint['annotation_list']):
                    if annotation['annotator'] == annotator_user_id:
                        added = True
                        self.__annotation_list[datapoint_idx][
                            'annotation_list'][annotation_idx] = labels
        if not added and index != -1 and index < len(self.__annotation_list):
            self.__annotation_list[index]['annotation_list'].append(labels)
        return labels

    def get_reconciliation_data(self, uuid_list=None):
        if uuid_list is None:
            uuid_list = []
            if self.__annotation_list is None:
                self.get_annotation_list()
            for annotation in self.__annotation_list:
                uuid_list.append(annotation['uuid'])
        return self.__service.get_reconciliation_data(uuid_list=uuid_list)

    def suggest_similar(self, meta_name, limit=3):
        payload = self.__service.get_base_payload()
        payload.update({
            'uuid_list': self.__data_uuids,
            "meta_name": meta_name,
            "limit": limit
        })
        path = self.__service.get_service_endpoint(
            'suggest_similar_annotations')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            suggested_uuids = list(set(json.loads(response.text)))
            return Subset(service=self.__service, data_uuids=suggested_uuids)
        else:
            raise Exception(response.text)