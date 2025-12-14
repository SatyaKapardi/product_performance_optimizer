"""Main application entry point"""
import socket
from dashboard import app

def find_free_port(start_port=8050):
    """Find a free port starting from start_port"""
    port = start_port
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
            port += 1

if __name__ == '__main__':
    port = find_free_port(8050)
    print(f"\n{'='*60}")
    print(f"Dashboard running on http://localhost:{port}/")
    print(f"{'='*60}\n")
    app.run_server(debug=True, host='0.0.0.0', port=port)

