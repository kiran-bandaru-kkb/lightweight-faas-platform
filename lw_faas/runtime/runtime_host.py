#!/usr/bin/env python3
"""
AryaXAI FaaS Platform - Generic Runtime Host
Executes a user's Python function in response to HTTP POST requests.
"""

import importlib.util
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import signal

# Configuration from Environment Variables
USER_FUNCTION_PATH = os.getenv('USER_FUNCTION_PATH')
FUNCTION_HANDLER_NAME = os.getenv('FUNCTION_HANDLER_NAME', 'handle')
RUNTIME_HOST_PORT = int(os.getenv('RUNTIME_HOST_PORT', '8080'))
INSTANCE_ID = os.getenv('INSTANCE_ID')  # Provided by the orchestrator

# Global reference to the loaded user function
user_function = None


class FunctionRequestHandler(BaseHTTPRequestHandler):
    """HTTP Handler that passes the request body to the user's function."""

    def do_POST(self):
        """Handle POST requests to execute the function."""
        if self.path != '/':
            self.send_error(404, "Endpoint not found. Use POST '/'.")
            return

        # 1. Read the request body
        content_length = int(self.headers.get('Content-Length', 0))
        request_body = self.rfile.read(content_length).decode('utf-8')

        # 2. Prepare a context object (optional but useful for the function)
        context = {
            'request_id': self.headers.get('X-Request-ID'),
            'instance_id': INSTANCE_ID,
        }

        # 3. Call the user's function with the request body
        try:
            # Parse JSON if possible, else pass raw string
            try:
                parsed_body = json.loads(request_body) if request_body else {}
            except json.JSONDecodeError:
                parsed_body = request_body

            # This is the crucial execution line
            result = user_function(parsed_body, context)

            # 4. Format the successful response
            response_body = json.dumps(result).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)

        except Exception as e:
            # 5. Handle any errors in the user's function gracefully
            error_response = {
                "error": "Function execution failed",
                "message": str(e),
                "type": e.__class__.__name__
            }
            response_body = json.dumps(error_response).encode('utf-8')
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(response_body)))
            self.end_headers()
            self.wfile.write(response_body)
            # Log the error for debugging
            print(f"ERROR: User function raised an exception: {e}", file=sys.stderr)

    def log_message(self, format, *args):
        # Suppress the default HTTP server log for cleaner output
        # You could send this to a structured logger in a real implementation
        pass


def load_user_function(module_path, function_name):
    """
    Dynamically load a Python function from a specified file.
    """
    global user_function

    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Function code not found at path: {module_path}")

    # Generate a unique module name to avoid collisions
    module_name = f"user_function_{hash(module_path)}"

    # Load the spec and module from the file
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None:
        raise ImportError(f"Could not load spec from file: {module_path}")
    module = importlib.util.module_from_spec(spec)

    # Execute the module to load its functions and variables
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ImportError(f"Failed to execute module {module_path}: {e}")

    # Get a reference to the user's function
    user_function = getattr(module, function_name, None)
    if user_function is None:
        raise AttributeError(f"Function '{function_name}' not found in {module_path}")
    if not callable(user_function):
        raise TypeError(f"'{function_name}' in {module_path} is not a callable function.")

    print(f"Successfully loaded function '{function_name}' from {module_path}")
    return user_function


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\nReceived signal {signum}. Shutting down runtime host.")
    sys.exit(0)


if __name__ == '__main__':
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Validate critical environment variable
    if not USER_FUNCTION_PATH:
        print("ERROR: Environment variable USER_FUNCTION_PATH is not set.", file=sys.stderr)
        sys.exit(1)

    print(f"Starting AryaXAI Runtime Host on port {RUNTIME_HOST_PORT}")
    print(f"Loading user function from: {USER_FUNCTION_PATH}")
    print(f"Expected handler function: {FUNCTION_HANDLER_NAME}")

    try:
        # Load the user's function. This will crash if it fails, which is intended.
        load_user_function(USER_FUNCTION_PATH, FUNCTION_HANDLER_NAME)
    except Exception as e:
        print(f"FATAL: Failed to load user function: {e}", file=sys.stderr)
        sys.exit(1)

    # Start the HTTP server
    httpd = HTTPServer(('', RUNTIME_HOST_PORT), FunctionRequestHandler)
    print(f"Server started. Listening on port {RUNTIME_HOST_PORT}. Ready to execute requests.")

    # Notify the orchestrator that we are ready (this would be a network call in a real system)
    # For the PoC, we just print it.
    if INSTANCE_ID:
        print(f"INSTANCE_READY: ID={INSTANCE_ID}, PORT={RUNTIME_HOST_PORT}")

    try:
        # Serve requests forever until interrupted
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        print("Runtime host stopped.")