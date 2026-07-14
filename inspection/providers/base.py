class BaseProvider:
    def search(self, request, query_params: dict) -> dict:
        raise NotImplementedError()
