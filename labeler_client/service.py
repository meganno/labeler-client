import asyncio
import base64
import json
import math
import time
import warnings

import httpx
import pandas as pd
from tqdm import tqdm

from labeler_client.constants import (DEFAULT_LIST_LIMIT, DNS_NAME,
                                      HTTPX_LIMITS, REQUEST_TIMEOUT_SECONDS,
                                      SERVICE_ENDPOINTS)
from labeler_client.helpers import get_request, post_request
from labeler_client.schema import Schema
from labeler_client.statistic import Statistic
from labeler_client.subset import Subset


class Service:
    """
    Service objects communicate to back-end Labeler services and establish
    connections to a Labeler project.


    """

    def __init__(self, host=None, project=None, token="", auth=None):
        """
        Init function

        Parameters
        -------
        host : str, optional
            Host IP address for the back-end service to connect to.
            If None, connects to Megagon-hosted service.
        project : str
            Project name. The name needs to be unique within the host
            domain.
        token : str
            User's authentication token.
        auth : Authentication
            [Megagon-only] Labeler-ui authentication object.
            Can be skipped if valid token is provided.
        """
        if project is None or len(project) == 0:
            raise Exception("Project cannot be None or empty.")
        if (token is None or len(token) == 0) and auth is None:
            raise Exception("At least 1 authentication method is required.")
        self.project = project
        self.token = token
        self.auth = auth
        self.host = host
        self.user = None
        response = get_request(
            path=self.get_service_endpoint() + "?url_check=1", timeout=5
        )
        if response.status_code != 200:
            raise Exception(response.text)

    def show(self):
        """
        Show project management dashboard in a floating dashboard.

        """
        from labeler_ui.widgets.Dashboard import Dashboard

        current_time = int(time.time())
        service_ref = f"service_ref_{current_time}"
        setattr(Service, service_ref, self)
        return Dashboard(service=service_ref).show()

    def __get_token(self):
        """
        Get token. If authentication object is used to initialize
        the service object, retrieve corresponding user token.
        """
        try:
            if self.token is not None and len(self.token) > 0:
                return ["access_token", self.token]
            elif self.auth is not None:
                return ["id_token", self.auth.get_id_token()]
        except:
            return ["", ""]
        return ["", ""]

    def get_service_endpoint(self, key=None):
        """
        Get REST endpoint for the connected project.
        Endpoints are composed from base project url and routes for
        specific requests.

        Parameters
        -------
        key : str
            Name of the specific request. Mapping to routes is stored in
            a dictionary `SERVICE_ENDPOINTS` in `constants.py`.

        """
        dns_name = DNS_NAME
        if self.host is not None:
            dns_name = self.host
        return (
            "{}:5000/".format(dns_name) + self.project + SERVICE_ENDPOINTS.get(key, "")
        )

    def get_base_payload(self):
        """
        Get the base payload for any REST request which includes the authentication token.
        """
        token_type, token = self.__get_token()
        return {token_type: token}

    def get_schemas(self):
        """
        Get schema object for the connected project.
        """
        return Schema(service=self)

    def get_project_info(self):
        """
        Get basic project information like name and descriptions.
        """
        path = self.get_service_endpoint("get_project_by_name").format(
            project_name=self.project
        )
        payload = self.get_base_payload()
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def __parse_id_token(self, token: str) -> dict:
        parts = token.split(".")
        if len(parts) != 3:
            raise Exception("Incorrect ID token format.")
        payload = parts[1]
        padded = payload + "=" * (4 - len(payload) % 4)
        decoded = base64.b64decode(padded)
        return json.loads(decoded)

    def get_statistics(self):
        """
        Get the statistics object for the project which supports
        calculations in the management dashboard.
        """
        return Statistic(service=self)

    def get_users_by_uid(self, uid_list: list = []):
        """
        Get user names by their unique IDs.
        Parameters
        -------
        uid_list : list
            list of unique user IDs.
        """
        if len(uid_list) > 0:
            path = self.get_service_endpoint("get_users_by_uid")
            payload = self.get_base_payload()
            payload.update({"uid_list": uid_list})
            response = get_request(path, json=payload)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(response.text)
        return {}

    def get_annotator(self):
        """
        Get annotator's own name and user ID.
        The back-end service distinguishes annotator by the
        token or auth object used to initialize the connection.
        """

        if self.user is None:
            if self.token is not None and len(self.token) > 0:
                path = self.get_service_endpoint("get_user")
                payload = self.get_base_payload()
                response = get_request(path, json=payload)
                if response.status_code == 200:
                    parsed_result = response.json()
                else:
                    raise Exception(response.text)
            elif self.auth is not None:
                parsed_result = self.__parse_id_token(token=self.auth.get_id_token())
            self.user = {
                "name": parsed_result.get("name"),
                "user_id": parsed_result.get("user_id"),
            }
        return self.user

    def __get_data(
        self,
        class_type,
        limit=DEFAULT_LIST_LIMIT,
        start=0,
        uuid_list=None,
        keyword="",
        label=None,
        regex="",
        meta_names: list = [],
    ):
        payload = self.get_base_payload()
        filter = {
            "keyword": keyword,
            "label": label,
            "limit": limit,
            "start": start,
            "uuid_list": uuid_list,
            "regex": regex,
        }
        payload.update(filter)
        response = get_request(self.get_service_endpoint("get_data"), json=payload)
        if response.status_code == 200:
            if class_type == "subset":
                return Subset(
                    data_uuids=response.json(),
                    meta_names=meta_names,
                    service=self,
                    annotator_id=self.get_annotator()["user_id"],
                )
        else:
            raise Exception(response.text)

    def search_by_job(
        self,
        limit=DEFAULT_LIST_LIMIT,
        start=0,
        job_id=None,
        verified=None,
    ):
        payload = self.get_base_payload()
        verified_status = "ALL"
        if verified is None:
            verified_status = "ALL"
        elif verified is True:
            verified_status = "VERIFIED"
        elif verified is False:
            verified_status = "UNVERIFIED"
        payload.update(
            {
                "verified_status": verified_status,
                "limit": limit,
                "start": start,
                "job_id": job_id,
            }
        )
        response = get_request(
            self.get_service_endpoint("get_data_by_job").format(job_uuid=job_id),
            json=payload,
        )
        if response.status_code == 200:
            return Subset(data_uuids=response.json(), service=self, job_id=job_id)
        else:
            raise Exception(response.text)

    def search(
        self,
        limit=DEFAULT_LIST_LIMIT,
        start=0,
        uuid_list=None,
        keyword="",
        label=None,
        regex="",
        meta_names: list = [],
    ):
        """
        Search the back-end database based on user-provided predicates.
        Parameters
        ------
        limit : int
            The limit of returned records in the subest.
        start : int
            Start index of returned subset
            (excluding the first `start` rows from the raw results ordered by importing order).
            Same as SQL skip parameter. TODO: rename to skip (here and in service)
        keyword : str
            Term for exact keyword searches.
        label : object
            Object containing `label_name` (strig) and list `label_value` (list) fields.
            Search results will be filtered to only contain records having `label_name` labels
            with values in the `label_value` list.
            Example:
            ```json
            --8<-- "docs/assets/code/search_label.json"
            ```
        regex : str
            Term for regular expression searches.
        meta_names : list
            list of meta_names. If not empty, the returned subset will also retrieve
            the corresponding metadata.

        Returns
        -------
        subset : Subset
            Subset containing data records (and optionally metadata) meeting the search conditions.

        """

        return self.__get_data(
            class_type="subset",
            limit=limit,
            start=start,
            uuid_list=uuid_list,
            keyword=keyword,
            label=label,
            regex=regex,
            meta_names=meta_names,
        )

    def submit_annotations(self, subset=None, uuid_list=[]):
        """
        Submit annotations for records in a subset to the back-end service database.
        Results are filtered to only include annotations owned by the authenticated
        annotator.

        Parameters
        -------
        subset : Subset
            The subset object containing records and annotations.
        uuid_list : list
            Additional filter. Only subset records whose uuid are in this list
            will be submitted.

        """
        if subset is None:
            raise Exception("Subset can not be None.")
        annotator_user_id = self.get_annotator()["user_id"]
        client = httpx.AsyncClient(limits=HTTPX_LIMITS, timeout=REQUEST_TIMEOUT_SECONDS)

        async def submit_annotation_by_uuid(uuid):
            annotation_data = subset.get_annotation_by_uuid(uuid)
            if annotation_data is not None:
                payload = self.get_base_payload()
                own = list(
                    filter(
                        lambda annotation: annotation["annotator"] == annotator_user_id,
                        annotation_data["annotation_list"],
                    )
                )
                payload.update({"labels": {} if len(own) == 0 else own[0]})
                path = self.get_service_endpoint("set_annotations").format(uuid=uuid)
                try:
                    response = await client.post(path, json=payload)
                    if response.status_code == 200:
                        return response.json()
                    else:
                        return {"uuid": uuid, "error": response.text}
                except httpx.TimeoutException:
                    return {"uuid": uuid, "error": "408 Request Timeout"}
                except Exception as e:
                    return {"uuid": uuid, "error": str(e)}

        async def main():
            return await asyncio.gather(
                *[submit_annotation_by_uuid(uuid=uuid) for uuid in uuid_list]
            )

        return asyncio.run(main())

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
            payload.update({"uuid_list": uuids})
            response = get_request(
                self.get_service_endpoint("get_reconciliation_data"), json=payload
            )
            if response.status_code == 200:
                result += response.json()
            else:
                raise Exception(response.text)
        return result

    def get_data_content(self, uuid_list=[]):
        """
        Get the raw data content for specified records
        Parameters
        -----
        uuid_list : list[str]
            List of querying uuids.
        """
        payload = self.get_base_payload()
        payload.update(
            {
                "uuid_list": uuid_list,
            }
        )
        path = self.get_service_endpoint("get_data_content")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def import_data_url(self, url="", file_type=None, column_mapping={}):
        """
        Import data from a public url, currently only supporting csv files.
        Each row corresponds to a data record. The file needs at least two columns:
        one with a unique id for each row, and one with the raw data content.

        Parameters
        ----
        url : str
            Public url for csv file
        file_type : str
            Currently only supporting type 'CSV'
        column_mapping : dict
            Dictionary with fields `id` specifying id column name, and `content` specifying
            content column name. For example, with a csv file with two columns `index` and `tweet`:
            ```json
            --8<-- "docs/assets/code/column_mapping/basic.json"
            ```
        """
        payload = self.get_base_payload()
        payload.update(
            {"url": url, "file_type": file_type, "column_mapping": column_mapping}
        )
        path = self.get_service_endpoint("post_data")
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def import_data_df(self, df, column_mapping={}):
        """
        Import data from a pandas DataFrame.
        Each row corresponds to a data record. The dataframe needs at least two columns:
        one with a unique id for each row, and one with the raw data content.

        Parameters
        ----
        df : DataFrame
            Qualifying dataframe
        column_mapping : dict
            Dictionary with fields `id` specifying id column name, and `content` specifying
            content column name. Using a dataframe, users can import metadata at the same time.
            For example, with a csv file with two columns `index` and `tweet`, and a column `location`:
            ```json
            --8<-- "docs/assets/code/column_mapping/metadata.json"
            ```
            metadata with name `location` will be created for all imported data records.

        """

        if not isinstance(df, pd.DataFrame):
            raise Exception("df needs to be a valid pandas dataframe")
        filtered_columns = []
        if len(column_mapping) == 0:
            # defult mapping ,check for columns "id" and "content"
            if "id" in df.columns and "content" in df.columns:
                filtered_columns.extend(["id", "content"])
                column_mapping = {"id": "id", "content": "content"}
            else:
                raise Exception(
                    "Needs to provide valid column_mapping, or columns with name 'id' and 'content'."
                )
        else:
            if (
                column_mapping["id"] in df.columns
                and column_mapping["content"] in df.columns
            ):
                filtered_columns.extend(
                    [column_mapping["id"], column_mapping["content"]]
                )
            else:
                raise Exception(
                    "Needs to provide valid column_mapping with fields 'id' and 'content'."
                )
        if "metadata" in column_mapping:
            filtered_columns.append(column_mapping["metadata"])

        # filter columns to only send necessary columns.
        # fill nan values to make json serializable.

        df = df[filtered_columns].fillna("NaN")

        if len(df) > 1000:
            warnings.warn(
                "Try using 'import_data_url' for import; importing large datasets DataFrame is not advised.",
                RuntimeWarning,
            )
        payload = self.get_base_payload()
        payload.update(
            {
                "file_type": "DF",
                "df_dict": df.to_dict(orient="records"),
                "column_mapping": column_mapping,
            }
        )
        path = self.get_service_endpoint("post_data")
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def export(self):
        """
        Exporting function.
        Returns
        ----
        export_df : DataFrame
            A pandas dataframe with columns
            `'data_id', 'content', 'annotator',
            'label_name', 'label_value'` for all records in the project

        """
        payload = self.get_base_payload()
        path = self.get_service_endpoint("export_data")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return pd.DataFrame(
                json.loads(response.text),
                columns=[
                    "data_id",
                    "content",
                    "annotator",
                    "label_name",
                    "label_value",
                ],
            )
        else:
            raise Exception(response.text)

    def set_verification_data(self, verify_list=[]):
        result = []
        for each in verify_list:
            uuid = each["uuid"]
            annotator_id = each["annotator_id"]
            label_level = each["labels"][0]["label_level"]
            label_name = each["labels"][0]["label_name"]
            payload = self.get_base_payload()
            payload.update(
                {
                    "uuid": uuid,
                    "labels": each["labels"],
                    "label_level": label_level,
                    "label_name": label_name,
                    "annotator_id": annotator_id,
                }
            )
            path = self.get_service_endpoint("set_verification_data").format(uuid=uuid)
            response = post_request(path, json=payload)
            if response.status_code == 200:
                result.append(response.json())
            else:
                result.append({"uuid": uuid, "error": response.text})
        return result

    def set_reconciliation_data(self, recon_list=[]):
        result = []
        for each in recon_list:
            uuid = each["uuid"]
            payload = self.get_base_payload()
            payload.update(
                {"uuid": uuid, "labels": each["labels"], "annotator": "reconciliation"}
            )
            path = self.get_service_endpoint("set_reconciliation_data").format(
                uuid=uuid
            )
            response = post_request(path, json=payload)
            if response.status_code == 200:
                result.append(response.json())
            else:
                result.append({"uuid": uuid, "error": response.text})
        return result

    def __batch_update_metadata(self, meta_name, metadata_list):
        """
        Update database and set metadata in batch.
        Parameters
        ----
        meta_name : str
            Name of metadata
        metadata_list : list[dict]
            List of dictionary with fields `uuid` specifying uuid of the
            source data record, and `value` for the metadata value to store.
        """
        payload = self.get_base_payload()
        payload.update(
            {
                "meta_name": meta_name,
                "metadata_list": metadata_list,
            }
        )
        path = self.get_service_endpoint("batch_update_metadata")
        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(response.text)

    def set_metadata(self, meta_name, func, batch_size=500):
        """
        Set metadata for all records in the back-end database,
        based on user-defined function for metadata calculation.
        Parameters
        ------
        meta_name : str
            Name of the metadata. Will be used to identify and query the metadata.
        func : function(raw_content)
            Function which takes input the raw data content and returns the
            corresponding metadata (int, string, vectors...).
        batch_size : int
            Batch size for back-end database updates.

        Example
        ----
        ```python
        --8<-- "docs/assets/code/set_metadata.py"
        ```
        """
        n = self.get_statistics().get_label_progress()["total"]
        set_count = 0
        batch_number = math.ceil(float(n) / batch_size)

        with tqdm(
            total=batch_number, leave=True, desc="Metadata batches processed:"
        ) as tq:
            for i in range(batch_number):
                s = self.__get_data(
                    class_type="subset", limit=batch_size, start=i * batch_size
                )
                data_batch = self.get_data_content(s.get_uuid_list())
                for item in data_batch:
                    item["value"] = func(item["data"])

                res = self.__batch_update_metadata(meta_name, data_batch)
                set_count += int(res)
                tq.update()
        return f"Set metadata '{meta_name}' for {set_count} data record{'s' if set_count > 1 else ''}."

    def get_assignment(self, annotator=None, latest_only=False):
        """
        Get workload assignment for annotator.
        Parameters
        ------
        annotator : str
            User ID to query. If set to None, use ID of auth token holder.
        latest_only : bool
            If true, return only the last assignment for the user.
            Else, return the set of all assigned records.
        """
        payload = self.get_base_payload()
        payload["annotator"] = annotator
        payload["latest_only"] = latest_only
        path = self.get_service_endpoint("get_assignment")
        response = get_request(path, json=payload)

        unique_assignments = set({})
        if response.status_code == 200:
            for res in response.json():
                unique_assignments.update(res["uuid_list"])
            return Subset(data_uuids=list(unique_assignments), service=self)

        else:
            raise Exception(response.text)
