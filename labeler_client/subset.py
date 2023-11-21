import json
import time

from labeler_client.helpers import get_request, post_request


class Subset:
    """
    The Subset class is used to represent a group of data records

    Attributes
    ----------
    __data_uuids : list
        List of unique identifiers of data records in the subset.
    __service : Service
        Connected backend service
    __annotation_list : list
        Local cache of retrieved data and annotation information for
        records in the subset.
    __meta_names : list
        List of metadata names. Metadata records additional information
        about data records, like document length or sentence embedding vectors.


    """

    def __init__(
        self, service, data_uuids=[], meta_names=[], job_id=None, annotator_id=None
    ):
        """
        Init function

        Parameters
        -------
        service : Service
            Service-class object identifying the connected
            backend service and corresponding data storage
        data_uuids : list
            List of data uuid's to be included in the subset
        meta_names : list
            Optional list of meta names. If specified, the client
            can retrieve the corresponding metadata (e.g., document length, embeddings)
            for each data record.
            <tmp : we should give an example of meta names>
        """
        self.__data_uuids = data_uuids
        self.__service = service
        self.__meta_names = meta_names
        self.job_id = job_id
        self.annotator_id = annotator_id
        self.__annotation_list = self.__get_annotation_list()

    def get_annotator_id(self):
        if self.job_id is not None:
            return self.job_id
        return self.annotator_id

    def get_verification_annotations(
        self,
        label_name=None,
        label_level=None,
        annotator: str = None,
        verifiers: list = None,
        verified_status: str = None,
    ):
        if label_name is None or len(label_name) == 0:
            raise Exception("label_name cannot be None or empty.")
        if label_level is None or len(label_level) == 0:
            raise Exception("label_level cannot be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "uuid_list": self.__data_uuids,
                "label_name": label_name,
                "label_level": label_level,
                "annotator": annotator,
                "verifiers": verifiers,
                "verified_status": verified_status,
            }
        )
        path = self.__service.get_service_endpoint("get_verification_annotations")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    def get_uuid_list(self):
        """
        Get list of unique identifiers for all records in the subset.

        Returns
        -------
        __data_uuids : list
            List of data uuids included in Subset
        """
        return self.__data_uuids

    def __get_annotation_list(self):
        """
        Returns all annotation list for all data records in the subset

        Returns
        ------
        subset_annotation_list : list
            A list of data and annotation for each data record in the subset.
                For each item in the list, `uuid` uniquely identifies the data record,
                , `data` field stores raw content, and metadata stores additional information
                about the record if `__meta_names` is set for the subset object.
                `annotation_list` stores all annotations (by different annotators) and contains
                two lists 'labels_record' and 'labels_span' for labels at different level.


            Example
            ---------
            Example annotation list with for a single-record subset:
            ```json
            --8<-- "docs/assets/code/annotation_list.json"
            ```
        """
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "uuid_list": self.__data_uuids,
                "meta_names": self.__meta_names,
                "annotator_id": self.get_annotator_id(),
            }
        )
        path = self.__service.get_service_endpoint("get_annotations")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            self.__annotation_list = response.json()
            return self.__annotation_list
        else:
            raise Exception(response.text)

    def value(self):
        """
        Check for cached annotations
        Returns
        -------
        subset_annotation_list : list
            See `get_annotation_list` for description and example.
        """
        return self.__annotation_list

    def get_data_content(self):
        """
        Get the raw data content for all records in the subset
        """
        return self.__service.get_data_content(uuid_list=self.__data_uuids)

    def get_annotation_by_uuid(self, uuid):
        """
        Returns the annotation for a particular data record (specified by uuid)

        Parameters
        ----------
        uuid : str
            the uuid for the data record specified by user

        Returns
        -------
        annotation : dict
            Annotation for specified data record if it exists else None
        """
        for annotation in self.__annotation_list:
            if annotation["uuid"] == uuid:
                return annotation
        return None

    def show(self, config={}):
        """
        Visualize the current subset in an in-notebook annotation widget.

        Development note: initializing an Annotation widget, creating unique reference to
        the associated subset and service.

        Parameters
        ----------
        config : dict
            Configuration for default view of the widget.

                - view : "single" | "table", default "single"
                - mode : "annotating" | "reconciling", default "annotating"
                - title: default "Annotation"
                - height: default 300 (pixels)
        """
        from labeler_ui import Annotation

        current_time = int(time.time())
        # Create a Subset class-level reference to the subset and service object
        # used to init the annotation widget. Thus the UI widget will always have
        # a referring handle to the corresponding communication channel.
        subset_ref = "subset_ref_{}".format(current_time)
        service_ref = "service_ref_{}".format(current_time)
        # Set class variables
        setattr(Subset, subset_ref, self)
        setattr(Subset, service_ref, self.__service)
        return Annotation(subset=subset_ref, service=service_ref, config=config).show()

    def set_annotations(self, uuid=None, labels=None):
        """Sets the annotation for a particular data record with the specified label

        Parameters
        ----------
        uuid : str
            the uuid for the data record specified by user
        labels : dict
            The labels for the data record at record and span level, with the following structure:

                - "labels_record" : list
                    A list of record-level labels
                - "labels_span" : list
                    A list of span-level labels

                Examples
                -------

                Example of setting an annotation with the desired record and span level labels:
                ```json
                --8<-- "docs/assets/code/set_annotations.json"
                ```

        Raises
        ------
        Exception
            If uuid or labels is None

        Returns
        -------
        labels : dict
            Updated labels for uuid annotated by user
        """
        annotator_user_id = self.__service.get_annotator()["user_id"]
        if uuid is None:
            raise Exception("UUID can not be None.")
        elif labels is None:
            raise Exception(
                f"Labels can not be None. For clearing annotations, use {{}}."
            )
        labels["annotator"] = annotator_user_id
        added = False
        index = -1
        for datapoint_idx, datapoint in enumerate(self.__annotation_list):
            if datapoint["uuid"] == uuid:
                index = datapoint_idx
                for annotation_idx, annotation in enumerate(
                    datapoint["annotation_list"]
                ):
                    if annotation["annotator"] == annotator_user_id:
                        added = True
                        self.__annotation_list[datapoint_idx]["annotation_list"][
                            annotation_idx
                        ] = labels
        if not added and index != -1 and index < len(self.__annotation_list):
            self.__annotation_list[index]["annotation_list"].append(labels)
        return labels

    def get_reconciliation_data(self, uuid_list=[]):
        """Returns the list of reconciliation data for all data entries specified by user.
        The reconciliation data for one data record consists of the annotations for it by all annotators

        Parameters
        ----------
        uuid_list : list
            list of uuid's provided by user

        Returns
        -------
        reconciliation_data_list : list
            List of reconciliation data for each uuid with the following keys: `annotation_list` which specifies all the annotations for the uuid, `data` which contains the raw data specified by the uuid, `metadata` which stores additional information about the data, `tokens` <tmp>, and the `uuid` of the data record
            Full Example:
            ```json
            --8<-- "docs/assets/code/reconciliation_data.json"
            ```
        """
        for annotation in self.__annotation_list:
            uuid_list.append(annotation["uuid"])
        return self.__service.get_reconciliation_data(uuid_list=uuid_list)

    def suggest_similar(self, meta_name, limit=3):
        """For each data record in the subset, suggest more similar data records
            by retriving the most similar data records from the pool, based on
            metadata(e.g., embedding) distance.
        Parameters
        ----------
        meta_name : str
            The meta-name eg. "bert-embedding" for which the similarity is calculated upon.
        limit : int
            The number of matching/similar records desired to be returned. Default is 3

        Raises
        ------
        Exception
            If response code is not successful

        Returns
        -------
        subset : Subset
            A subset of similar data entries
        """
        payload = self.__service.get_base_payload()
        payload.update(
            {"uuid_list": self.__data_uuids, "meta_name": meta_name, "limit": limit}
        )
        path = self.__service.get_service_endpoint("suggest_similar_annotations")
        response = get_request(path, json=payload)
        if response.status_code == 200:
            suggested_uuids = list(set(json.loads(response.text)))
            return Subset(service=self.__service, data_uuids=suggested_uuids)
        else:
            raise Exception(response.text)

    def assign(self, annotator):
        """
        Assign the current subset as payload to an annotator.
        Parameters
        ----------
        annotator : str
            Annotator ID.
        """
        if annotator is None or len(annotator) == 0:
            raise Exception("Annotator cannot be None or empty.")
        payload = self.__service.get_base_payload()
        payload.update(
            {
                "subset_uuid_list": self.__data_uuids,
                "annotator": annotator,
            }
        )
        path = self.__service.get_service_endpoint("get_assignment")

        response = post_request(path, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(response.text)

    # overlading subset operation with set algebra
    def __or__(self, other):
        """
        Computation overloading for the set "or" operator |.
        With Subset A and B, C = A | B will return a new Subset object
        with a uuid_list which unions data records in A and B.
        """
        return Subset(
            service=self.__service,
            data_uuids=list(set(self.get_uuid_list()) | set(other.get_uuid_list())),
        )

    def union(self, other):
        return Subset.__or__(self, other)

    def __and__(self, other):
        """
        Computation overloading for the set "and" operator &.
        With Subset A and B, C = A & B will return a new Subset object
        with a uuid_list which intersects data records in A and B.
        """
        return Subset(
            service=self.__service,
            data_uuids=list(set(self.get_uuid_list()) & set(other.get_uuid_list())),
        )

    def intersection(self, other):
        return Subset.__and__(self, other)

    def __sub__(self, other):
        return Subset(
            service=self.__service,
            data_uuids=list(set(self.get_uuid_list()) - set(other.get_uuid_list())),
        )

    def difference(self, other):
        return Subset.__sub__(self, other)
