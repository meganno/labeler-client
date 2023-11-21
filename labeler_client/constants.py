import httpx

SERVICE_ENDPOINTS = {
    "get_annotations": "/annotations",
    "set_annotations": "/annotations/{uuid}",
    "get_data": "/data",
    "get_data_by_job": "/data/jobs/{job_uuid}",
    "post_data": "/data",
    "get_data_content": "/data/content",
    "batch_update_metadata": "/data/metadata",
    "suggest_similar_annotations": "/annotations/suggest_similar",
    "export_data": "/data/export",
    "get_schemas": "/schemas",
    "set_schemas": "/schemas",
    "get_assignment": "/assignment",
    "set_assignment": "/assignment",
    "get_reconciliation_data": "/reconciliations",
    "set_reconciliation_data": "/annotations/{uuid}/labels",
    "set_verification_data": "/verifications/{uuid}/labels",
    "get_verification_annotations": "/verifications/annotations",
    "get_user": "/users",
    "get_users_by_uid": "/users/uid",
    "get_label_progress": "/statistics/label/progress",
    "get_label_distribution": "/statistics/label/distributions",
    "get_annotator_contribution": "/statistics/annotator/contributions",
    "get_annotator_agreement": "/statistics/annotator/agreements",
    "get_embeddings": "/statistics/embeddings/{embed_type}",
    "get_projects": "/projects",
    "archive_project": "/projects/{project_id}",
    "restore_project": "/projects/{project_id}",
    "get_project_by_name": "/projects/{project_name}",
    "create_project": "/projects",
    "get_project_stack_status": "/projects/stack_status",
    "get_agents": "/agents",
    "get_jobs_of_agent": "/agents/{agent_uuid}/jobs",
    "get_jobs": "/agents/jobs",
    "register_agent": "/agents",
    "set_job": "/agents/{agent_uuid}/jobs/{job_uuid}",
}
VALID_SCHEMA_LEVELS = ["span_ch", "record"]
NO_TIMEOUT_ENDPOINTS = {
    "post": [SERVICE_ENDPOINTS["post_data"]],
    "get": [SERVICE_ENDPOINTS["suggest_similar_annotations"]],
}
DEFAULT_LIST_LIMIT = 10
REQUEST_TIMEOUT_SECONDS = 10
DNS_NAME = "https://labeler.megagon.ai"
__BASE_WORKERS = 5
HTTPX_LIMITS = httpx.Limits(max_connections=__BASE_WORKERS + 1)
