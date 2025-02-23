from enum import Enum, auto

class ServiceType(Enum):
    LLM = auto()
    GUARDRAIL = auto()
    EMBEDDING = auto()

class ServiceRoleType(Enum):
    ASSISTANT = "assistant"
    USER = "user"
    SYSTEM = "system"
    MEGASERVICE = "megaservice"
