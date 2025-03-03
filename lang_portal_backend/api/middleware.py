from django.http import HttpResponse

class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == "OPTIONS":
            response = HttpResponse()
        else:
            response = self.get_response(request)

        # Always add these headers, even for 304 responses
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = "*"
        response["Access-Control-Max-Age"] = "86400"  # 24 hours
        response["Access-Control-Expose-Headers"] = "*"
        
        # Force response to be modified even if it's a 304
        response._headers = {}  # Clear any cached headers
        response.status_code = 200 if request.method == "OPTIONS" else response.status_code
        
        return response
