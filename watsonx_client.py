import os
from dotenv import load_dotenv
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference
from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

load_dotenv() 
MODEL_ID = "meta-llama/llama-3-3-70b-instruct"


def get_model(max_tokens=500, temperature=0.3):
    """Returns a ready-to-use watsonx model client."""
    credentials = Credentials(
        url=os.environ["WATSONX_URL"],
        api_key=os.environ["WATSONX_API_KEY"],
    )
    params = {
        GenParams.MAX_NEW_TOKENS: max_tokens,
        GenParams.TEMPERATURE: temperature,
    }
    return ModelInference(
        model_id=MODEL_ID,
        credentials=credentials,
        project_id=os.environ["WATSONX_PROJECT_ID"],
        params=params,
    )
