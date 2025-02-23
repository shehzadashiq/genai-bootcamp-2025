from fastapi import FastAPI
import uvicorn
from typing import Optional, List, Any, Callable

class MicroService:
    def __init__(self, name, host, port, endpoint, use_remote_service=True, service_type=None, service_role=None, input_datatype=None, output_datatype=None):
        self.name = name
        self.host = host
        self.port = port
        self.endpoint = endpoint
        self.use_remote_service = use_remote_service
        self.service_type = service_type
        self.service_role = service_role
        self.input_datatype = input_datatype
        self.output_datatype = output_datatype
        self.app = FastAPI()

    def add_route(self, path: str, endpoint_func: Callable[..., Any], methods: Optional[List[str]] = None):
        """Add a route to the FastAPI application.
        
        Args:
            path (str): URL path for the endpoint
            endpoint_func: Async function to handle the request
            methods (list): HTTP methods to support
        """
        if methods is None:
            methods = ["GET"]
            
        for method in methods:
            self.app.add_api_route(
                path=path,
                endpoint=endpoint_func,
                methods=[method],
                response_model=self.output_datatype
            )

    @property
    def fastapi_app(self):
        """Expose the FastAPI app"""
        return self.app

    def start(self):
        """Start the FastAPI server."""
        uvicorn.run(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )

class ServiceOrchestrator:
    def __init__(self):
        self.services = {}
        self.flows = {}  # Store service flows
    
    def add(self, service: MicroService):
        """Add a service to the orchestrator.
        
        Args:
            service (MicroService): The service to add
            
        Returns:
            ServiceOrchestrator: Returns self for method chaining
        """
        if not isinstance(service, MicroService):
            raise TypeError("Service must be an instance of MicroService")
        
        self.services[service.name] = service
        return self  # Enable method chaining
    
    def flow_to(self, from_service: MicroService, to_service: MicroService):
        """Define a flow between two services.
        
        Args:
            from_service (MicroService): Source service
            to_service (MicroService): Target service
            
        Returns:
            ServiceOrchestrator: Returns self for method chaining
        """
        if not isinstance(from_service, MicroService) or not isinstance(to_service, MicroService):
            raise TypeError("Both services must be instances of MicroService")
            
        if from_service.name not in self.services or to_service.name not in self.services:
            raise ValueError("Both services must be added to the orchestrator first")
            
        if from_service.name not in self.flows:
            self.flows[from_service.name] = []
            
        self.flows[from_service.name].append(to_service.name)
        return self
