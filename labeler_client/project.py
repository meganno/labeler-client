from importlib.resources import path
from labeler_client.constants import DNS_NAME, SERVICE_ENDPOINTS
from labeler_ui import ProjectManager
from labeler_client.helpers import get_request, post_request
import sys


class Project:

    def __init__(self, host=None, token='', auth=None):
        if (token is None or len(token) == 0) and auth is None:
            raise Exception("At least 1 authentication method is required.")
        self.token = token
        self.auth = auth
        self.host = host
        self.project_exists = False

    def get_service_endpoint(self, key=None):
        dns_name = DNS_NAME
        if self.host is not None:
            dns_name = self.host
        return '{}:5000/'.format(
            dns_name) + 'development' + SERVICE_ENDPOINTS.get(key, '')

    def get_variable_name(self, target=None):
        if target is None:
            return None
        for name, module in sys.modules.items():
            try:
                for varname, obj in module.__dict__.items():
                    if obj is target:
                        return varname
            except AttributeError:
                pass
        return None

    def get_base_payload(self):
        token_type, token = self.__get_token()
        return {token_type: token}

    def __get_token(self):
        try:
            if self.token is not None and len(self.token) > 0:
                return ['access_token', self.token]
            elif self.auth is not None:
                return ['id_token', self.auth.get_id_token()]
        except:
            return ['', '']
        return ['', '']

    def get_project_stack_status(self, stack_id):
        payload = self.get_base_payload()
        payload.update({'stack_id': stack_id})
        path = self.get_service_endpoint('get_project_stack_status')
        response = get_request(path=path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def create_project(self, name=''):
        payload = self.get_base_payload()
        payload.update({'project_name': name})
        path = self.get_service_endpoint('create_project')
        response = post_request(path=path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_projects(self):
        payload = self.get_base_payload()
        path = self.get_service_endpoint('get_projects')
        response = get_request(path=path, json=payload)
        if response.status_code == 200:
            result = {}
            for project in response.json():
                result[project] = {
                    'REST_API': f'{DNS_NAME}:5000/{project}?url_check=1'
                }
            return result
        else:
            raise Exception(response.text)

    def show(self):
        project_varname = self.get_variable_name(target=self)
        widget = ProjectManager(project=project_varname)
        return widget.show()