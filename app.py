%pip install "openai==1.70.0"
%pip install "synapseml==1.0.5"
%pip install pandas tqdm 


import typing as t
import uuid
from openai import OpenAI
from openai._models import FinalRequestOptions
from openai._types import Omit
from openai._utils import is_given
from synapse.ml.mlflow import get_mlflow_env_config
 
base_url = "https://api.fabric.microsoft.com/v1/workspaces/27123242-df72-41f7-822b-0b14db152c20/aiskills/8d9fd5…
question = "What is the lowest and highest date in the 'DimDate' table"
configs = get_mlflow_env_config()
 
class FabricOpenAI(OpenAI):
    def _init_(self, api_version: str = "2024-05-01-preview", **kwargs: t.Any) -> None:
        default_query = kwargs.pop("default_query", {})
        default_query["api-version"] = api_version
        super()._init_(api_key="", base_url=base_url, default_query=default_query, **kwargs)
 
    def _prepare_options(self, options: FinalRequestOptions) -> None:
        headers = {**options.headers} if is_given(options.headers) else {}
        headers["Authorization"] = f"Bearer {configs.driver_aad_token}"
        headers.setdefault("Accept", "application/json")
        headers.setdefault("ActivityId", str(uuid.uuid4()))
        options.headers = headers
        return super()._prepare_options(options)
 
fabric_client = FabricOpenAI()
assistant = fabric_client.beta.assistants.create(model="not used")
thread = fabric_client.beta.threads.create()
fabric_client.beta.threads.messages.create(thread_id=thread.id, role="user", content=question)
run = fabric_client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
 
while run.status != "completed":
    run = fabric_client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
 
for m in fabric_client.beta.threads.messages.list(thread_id=thread.id, order="asc"):
    for c in m.content:
        print(f"{m.role}: {c.text.value}")
