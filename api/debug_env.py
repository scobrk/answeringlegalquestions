"""
Debug endpoint to test environment variable access in Vercel
"""

import os
import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    """Debug environment variables in Vercel runtime"""

    def do_GET(self):
        """Check if environment variables are accessible"""
        try:
            # Get all environment variables
            env_vars = dict(os.environ)

            # Check specific variables we need
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            openai_key = os.getenv('OPENAI_API_KEY')

            # Mask sensitive values for logging
            def mask_value(value):
                if value and len(value) > 8:
                    return value[:4] + '***' + value[-4:]
                return value or 'NOT_SET'

            debug_info = {
                'status': 'debug_success',
                'environment_variables': {
                    'SUPABASE_URL': mask_value(supabase_url),
                    'SUPABASE_KEY': mask_value(supabase_key),
                    'OPENAI_API_KEY': mask_value(openai_key)
                },
                'env_var_exists': {
                    'SUPABASE_URL': 'SUPABASE_URL' in env_vars,
                    'SUPABASE_KEY': 'SUPABASE_KEY' in env_vars,
                    'OPENAI_API_KEY': 'OPENAI_API_KEY' in env_vars
                },
                'os_environ_keys_count': len(env_vars),
                'vercel_specific_vars': {
                    key: mask_value(value) for key, value in env_vars.items()
                    if key.startswith('VERCEL_')
                },
                'python_version': env_vars.get('PYTHON_VERSION', 'unknown'),
                'runtime_info': {
                    'pwd': env_vars.get('PWD', 'unknown'),
                    'path': env_vars.get('PATH', 'unknown')[:100] + '...' if env_vars.get('PATH') else 'unknown'
                }
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(debug_info, indent=2).encode('utf-8'))

        except Exception as e:
            error_response = {
                'status': 'debug_error',
                'error': str(e),
                'error_type': type(e).__name__
            }

            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            self.wfile.write(json.dumps(error_response, indent=2).encode('utf-8'))