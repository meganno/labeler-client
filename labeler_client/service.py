import sys, base64, json, math
from tqdm import tqdm
from labeler_client.helpers import get_request, post_request
from labeler_client.statistic import Statistic
from labeler_client.subset import Subset
from labeler_client.constants import DNS_NAME, SERVICE_ENDPOINTS, DEFAULT_LIST_LIMIT
from labeler_client.schema import Schema
import pandas as pd


class Service:

    def __init__(self, host=None, project=None, token='', auth=None):
        if project is None or len(project) == 0:
            raise Exception("Project cannot be None or empty.")
        if (token is None or len(token) == 0) and auth is None:
            raise Exception("At least 1 authentication method is required.")
        self.project = project
        self.token = token
        self.auth = auth
        self.host = host
        response = get_request(path=self.get_service_endpoint() +
                               '?url_check=1',
                               timeout=5)
        if response.status_code != 200:
            raise Exception(response.text)

    def __get_token(self):
        try:
            if self.token is not None and len(self.token) > 0:
                return ['access_token', self.token]
            elif self.auth is not None:
                return ['id_token', self.auth.get_id_token()]
        except:
            return ['', '']
        return ['', '']

    def get_service_endpoint(self, key=None):
        dns_name = DNS_NAME
        if self.host is not None:
            dns_name = self.host
        return '{}:5000/'.format(
            dns_name) + self.project + SERVICE_ENDPOINTS.get(key, '')

    def get_base_payload(self):
        token_type, token = self.__get_token()
        return {token_type: token}

    def get_schemas(self):
        return Schema(service=self)

    def __parse_id_token(self, token: str) -> dict:
        parts = token.split(".")
        if len(parts) != 3:
            raise Exception("Incorrect ID token format.")
        payload = parts[1]
        padded = payload + '=' * (4 - len(payload) % 4)
        decoded = base64.b64decode(padded)
        return json.loads(decoded)

    def get_statistics(self):
        return Statistic(service=self)

    def get_users_by_uid(self, uid_list: list = []):
        if len(uid_list) > 0:
            path = self.get_service_endpoint('get_users_by_uid')
            payload = self.get_base_payload()
            payload.update({'uid_list': uid_list})
            response = get_request(path, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(response.text)
        return {}

    def get_annotator(self):

        if self.token is not None and len(self.token) > 0:
            path = self.get_service_endpoint('get_user')
            payload = self.get_base_payload()
            response = get_request(path, json=payload)
            if response.status_code == 200:
                parsed_result = response.json()
            else:
                raise Exception(response.text)
        elif self.auth is not None:
            parsed_result = self.__parse_id_token(
                token=self.auth.get_id_token())
        return {
            'name': parsed_result.get('name'),
            'user_id': parsed_result.get('user_id')
        }

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

    def __get_data(self,
                   class_type,
                   limit=DEFAULT_LIST_LIMIT,
                   start=0,
                   uuid_list=None,
                   keyword='',
                   label=None,
                   regex='',
                   meta_names: list = []):
        payload = self.get_base_payload()
        filter = {
            'keyword': keyword,
            'label': label,
            'limit': limit,
            'start': start,
            'uuid_list': uuid_list,
            'regex': regex
        }
        payload.update(filter)
        response = get_request(self.get_service_endpoint('get_data'),
                               json=payload)
        if response.status_code == 200:
            if class_type == 'subset':
                return Subset(data_uuids=response.json(),
                              meta_names=meta_names,
                              service=self)
        else:
            raise Exception(response.text)

    def search(self,
               limit=DEFAULT_LIST_LIMIT,
               start=0,
               uuid_list=None,
               keyword='',
               label=None,
               regex='',
               meta_names: list = []):
        return self.__get_data(class_type='subset',
                               limit=limit,
                               start=start,
                               uuid_list=uuid_list,
                               keyword=keyword,
                               label=label,
                               regex=regex,
                               meta_names=meta_names)

    def submit_annotations(self, subset=None, uuid_list=[]):
        if subset is None:
            raise Exception('Subset can not be None.')
        annotator_user_id = self.get_annotator()['user_id']
        result = []
        for uuid in uuid_list:
            data = subset.get_data_by_uuid(uuid)
            if data is not None:
                payload = self.get_base_payload()
                own = list(
                    filter(
                        lambda annotation: annotation['annotator'] ==
                        annotator_user_id, data['annotation_list']))
                payload.update({'labels': {} if len(own) == 0 else own[0]})
                path = self.get_service_endpoint('set_annotations').format(
                    uuid=uuid)
                response = post_request(path, json=payload)
                if response.status_code == 200:
                    result.append(response.json())
                else:
                    result.append({'uuid': uuid, 'error': response.text})
        return result

    def get_reconciliation_data(self, uuid_list=[]):
        if len(uuid_list) == 0:
            return []
        BATCH_SIZE = 45
        # making sure the request URL doesn't exceed the 2048 characters limitation for certain browsers
        index = 0
        result = []
        while index < len(uuid_list):
            uuids = []
            counter = 0
            while index < len(uuid_list) and counter < BATCH_SIZE:
                counter += 1
                uuids.append(uuid_list[index])
                index += 1
            payload = self.get_base_payload()
            payload.update({'uuid_list': uuids})
            response = get_request(
                self.get_service_endpoint('get_reconciliation_data'),
                json=payload)
            if response.status_code == 200:
                result += response.json()
            else:
                raise Exception(response.text)
        return result

    def get_data_content(self, uuid_list=[]):
        payload = self.get_base_payload()
        payload.update({
            'uuid_list': uuid_list,
        })
        path = self.get_service_endpoint('get_data_content')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def import_data_url(self, url='', file_type=None, column_mapping={}):
        payload = self.get_base_payload()
        payload.update({
            'url': url,
            'file_type': file_type,
            'column_mapping': column_mapping
        })
        path = self.get_service_endpoint('post_data')
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def import_data_df(self, df, column_mapping={}):
        if not isinstance(df, pd.DataFrame):
            raise Exception("df needs to be a valid pandas dataframe")
        filtered_columns = []
        if len(column_mapping) == 0:
            # defult mapping ,check for columns "id" and "content"
            if "id" in df.columns and "content" in df.columns:
                filtered_columns.extend(['id', 'content'])
                column_mapping = {'id': 'id', 'content': 'content'}
            else:
                raise Exception(
                    "Needs to provide valid column_mapping, or columns with name 'id' and 'content'."
                )
        else:
            if column_mapping["id"] in df.columns and column_mapping[
                    "content"] in df.columns:
                filtered_columns.extend(
                    [column_mapping["id"], column_mapping["content"]])
            else:
                raise Exception(
                    "Needs to provide valid column_mapping with fields 'id' and 'content'."
                )
        if "metadata" in column_mapping:
            filtered_columns.append(column_mapping['metadata'])

        # filter columns to only send necessary columns.
        # fill nan values to make json serializable.

        df = df[filtered_columns].fillna("NaN")

        if len(df) > 1000:
            print(
                "Warning: dataframe loading is not advised for larger datasets, try loading from url using 'import_data' "
            )
        payload = self.get_base_payload()
        payload.update({
            'file_type': "DF",
            'df_dict': df.to_dict(orient='records'),
            'column_mapping': column_mapping
        })
        path = self.get_service_endpoint('post_data')
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def export(self):
        payload = self.get_base_payload()
        path = self.get_service_endpoint('export_data')
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return pd.DataFrame(json.loads(response.text),
                                columns=[
                                    'data_id', 'content', 'annotator',
                                    'label_name', 'label_value'
                                ])
        else:
            raise Exception(response.text)

    def set_reconciliation_data(self, recon_list=[]):
        result = []
        for each in recon_list:
            uuid = each['uuid']
            payload = self.get_base_payload()
            payload.update({
                'uuid': uuid,
                'labels': each['label'],
                'annotator': 'reconciliation'
            })
            path = self.get_service_endpoint('set_reconciliation_data').format(
                uuid=uuid)
            response = post_request(path, json=payload)
            if response.status_code == 200:
                result.append(response.json())
            else:
                result.append({'uuid': uuid, 'error': response.text})
        return result

    def batch_update_metadata(self, meta_name, metadata_list):
        payload = self.get_base_payload()
        payload.update({
            'meta_name': meta_name,
            'metadata_list': metadata_list,
        })
        path = self.get_service_endpoint('batch_update_metadata')
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def set_metadata(self, meta_name, func, batch_size=500):
        n = self.get_statistics().get_label_progress()['total']
        set_count = 0
        batch_number = math.ceil(float(n) / batch_size)

        with tqdm(total=batch_number,
                  leave=True,
                  desc='Metadata batches processed:') as tq:
            for i in range(batch_number):
                s = self.__get_data(class_type='subset',
                                    limit=batch_size,
                                    start=i * batch_size)
                data_batch = json.loads(
                    self.get_data_content(s.get_uuid_list()))
                for item in data_batch:
                    item['value'] = func(item['content'])
                res = self.batch_update_metadata(meta_name, data_batch)
                set_count += int(res)
                tq.update()

        print("Finished setting metadata {} for {} data records".format(
            meta_name, set_count))
        return

    def get_assignment(self, annotator=None, latest_only=False):
        '''
        Get subset assignment for annotator.
        :param annotator: querying annotator user id, token holder if None
        '''
        payload = self.get_base_payload()
        payload['annotator'] = annotator
        payload['latest_only'] = latest_only
        path = self.get_service_endpoint('get_assignment')
        response = get_request(path, json=payload)

        unique_assignments = set({})
        if response.status_code == 200:
            for res in response.json():
                unique_assignments.update(res['uuid_list'])
            return Subset(data_uuids=list(unique_assignments), service=self)

        else:
            raise Exception(response.text)