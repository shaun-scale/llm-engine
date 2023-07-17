from llmengine.api_engine import DEFAULT_TIMEOUT, APIEngine, assert_self_hosted
from llmengine.data_types import (
    CreateLLMModelEndpointV1Request,
    CreateLLMModelEndpointV1Response,
    DeleteLLMEndpointResponse,
    GetLLMEndpointResponse,
    ListLLMEndpointsResponse,
)


class Model(APIEngine):
    """
    Model API. This API is used to retrieve, list, remove, and (in the self-hosted case) create models. When using Scale Spellbook, create models using FineTune.create().


    Example:
        ```python
        from llmengine import Model

        response = Model.list()
        print(response)
        ```
    """

    @classmethod
    @assert_self_hosted
    def create(
        cls,
        model_name: str,
    ) -> CreateLLMModelEndpointV1Response:
        """
        Create a Model Endpoint. Note: This feature is only available for self-hosted users.

        Args:
            model_name (`str`):
                Name of the model

        Returns:
            response: ID of the created Model Endpoint.
        """
        request = CreateLLMModelEndpointV1Request(
            model_name=model_name,
        )
        response = cls.post_sync(
            resource_name="v1/llm/model-endpoints",
            data=request.dict(),
            timeout=DEFAULT_TIMEOUT,
        )
        return CreateLLMModelEndpointV1Response.parse_obj(response)

    @classmethod
    def retrieve(
        cls,
        model_name: str,
    ) -> GetLLMEndpointResponse:
        """
        Get an LLM model endpoint

        Args:
            model_name (`str`):
                Name of the model

        Returns:
            response: object representing the LLM endpoint and configurations
        """
        response = cls.get(f"v1/llm/model-endpoints/{model_name}", timeout=DEFAULT_TIMEOUT)
        return GetLLMEndpointResponse.parse_obj(response)

    @classmethod
    def list(cls) -> ListLLMEndpointsResponse:
        """
        List model endpoints

        Returns:
            response: list of model endpoints
        """
        response = cls.get("v1/llm/model-endpoints", timeout=DEFAULT_TIMEOUT)
        return ListLLMEndpointsResponse.parse_obj(response)

    @classmethod
    def remove(cls, model_name: str) -> DeleteLLMEndpointResponse:
        """
        Deletes an LLM model endpoint

        Args:
            model_name (`str`):
                Name of the model

        Returns:
            response: whether the model was successfully deleted
        """
        response = cls.delete(f"v1/llm/model-endpoints/{model_name}", timeout=DEFAULT_TIMEOUT)
        return DeleteLLMEndpointResponse.parse_obj(response)
