from abc import ABC, abstractmethod


class IUseCase[InputDTO, OutputDTO](ABC):
    @abstractmethod
    async def execute(self, *, input_dto: InputDTO) -> OutputDTO:
        raise NotImplementedError
