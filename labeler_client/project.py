import time

from labeler_client.constants import DNS_NAME, SERVICE_ENDPOINTS
from labeler_client.helpers import (delete_request, get_request, post_request,
                                    put_request)


class Project:
    """
    [Megagon-only] Methods for managing multi-project domains; with interfaces to create, list, archieve and restore projects.
    """

    def __init__(self, project='base', host=None, token='', auth=None):
        if host is not None:
            if project is None or len(project) == 0:
                raise Exception("Project cannot be None or empty.")
        if (token is None or len(token) == 0) and auth is None:
            raise Exception("At least 1 authentication method is required.")
        self.token = token
        self.project = project
        if host is None or len(host) == 0:
            self.project = 'base'
        self.auth = auth
        self.host = host
        self.project_exists = False

    def get_service_endpoint(self, key=None):
        dns_name = DNS_NAME
        if self.host is not None:
            dns_name = self.host
        return f'{dns_name}:5000/{self.project}{SERVICE_ENDPOINTS.get(key, "")}'

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

    def restore_project(self, id):
        payload = self.get_base_payload()
        payload.update({'id': id})
        path = self.get_service_endpoint('restore_project').format(
            project_id=id)
        response = put_request(path=path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def archive_project(self, id):
        payload = self.get_base_payload()
        payload.update({'id': id})
        path = self.get_service_endpoint('archive_project').format(
            project_id=id)
        response = delete_request(path=path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_projects(self, archived=False):
        payload = self.get_base_payload()
        payload.update({'archived': archived})
        path = self.get_service_endpoint('get_projects')
        response = get_request(path=path, json=payload)
        if response.status_code == 200:
            result = response.json()
            for i in range(len(result)):
                result[i] = {
                    **result[i],
                    'api':
                    f'{DNS_NAME}:5000/{result[i]["project_name"]}?url_check=1',
                }
            return result
        else:
            raise Exception(response.text)

    def show(self):
        from labeler_ui import ProjectManager
        current_time = int(time.time())
        project_ref = f'project_ref_{current_time}'
        setattr(Project, project_ref, self)
        return ProjectManager(project=project_ref).show()