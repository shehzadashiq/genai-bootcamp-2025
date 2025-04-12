import logging
import sys
import traceback
from django.http import JsonResponse
from rest_framework.decorators import api_view
import os
import io
from contextlib import redirect_stdout, redirect_stderr

logger = logging.getLogger(__name__)

@api_view(['GET'])
def debug_log_test(request):
    """
    Debug endpoint to test logging functionality.
    This bypasses the regular logging system and writes directly to stdout/stderr.
    """
    # Capture stdout and stderr
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    
    with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
        print("=" * 80)
        print("DIRECT STDOUT: Debug view called")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Python version: {sys.version}")
        print(f"DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
        print(f"DEBUG setting: {os.environ.get('DEBUG')}")
        
        # Print to stderr
        print("ERROR OUTPUT TEST", file=sys.stderr)
        
        # Try all logging levels
        logger.debug("DEBUG: This is a debug message from the debug view")
        logger.info("INFO: This is an info message from the debug view")
        logger.warning("WARNING: This is a warning message from the debug view")
        logger.error("ERROR: This is an error message from the debug view")
        logger.critical("CRITICAL: This is a critical message from the debug view")
        
        # Also try the root logger
        root_logger = logging.getLogger("")
        root_logger.debug("ROOT DEBUG: This is a debug message from the root logger")
        root_logger.info("ROOT INFO: This is an info message from the root logger")
        
        # Try a different logger
        django_logger = logging.getLogger("django")
        django_logger.debug("DJANGO DEBUG: This is a debug message from the django logger")
        django_logger.info("DJANGO INFO: This is an info message from the django logger")
        
        # Check logging configuration
        print("\nLogging Configuration:")
        print(f"Root logger level: {logging.getLogger().level}")
        print(f"Root logger handlers: {[h.__class__.__name__ for h in logging.getLogger().handlers]}")
        print(f"Django logger level: {logging.getLogger('django').level}")
        print(f"API logger level: {logging.getLogger('api').level}")
        
        # Check logging handlers
        print("\nHandler Details:")
        for handler in logging.getLogger().handlers:
            print(f"Handler: {handler.__class__.__name__}, Level: {handler.level}")
            if hasattr(handler, 'stream'):
                print(f"  Stream: {handler.stream}")
        
        print("=" * 80)
    
    # Get the captured output
    stdout_output = stdout_buffer.getvalue()
    stderr_output = stderr_buffer.getvalue()
    
    # Force output to console
    sys.__stdout__.write(stdout_output)
    sys.__stderr__.write(stderr_output)
    
    # Return a simple response with the captured output
    return JsonResponse({
        "message": "Debug log test executed. Check your console output.",
        "stdout": stdout_output,
        "stderr": stderr_output,
        "loggers": list(logging.Logger.manager.loggerDict.keys()),
        "handlers": {
            "root": [h.__class__.__name__ for h in logging.getLogger().handlers],
            "django": [h.__class__.__name__ for h in logging.getLogger("django").handlers] if "django" in logging.Logger.manager.loggerDict else [],
            "api": [h.__class__.__name__ for h in logging.getLogger("api").handlers] if "api" in logging.Logger.manager.loggerDict else [],
        },
        "request_path": request.path,
        "request_method": request.method,
        "request_headers": dict(request.headers),
    })
