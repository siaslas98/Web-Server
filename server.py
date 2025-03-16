import http.server
import os

PAGE = """\
<html>
<body>
<table>
<tr>  <td>Header</td>         <td>Value</td>          </tr>
<tr>  <td>Date and time</td>  <td>{date_time}</td>    </tr>
<tr>  <td>Client host</td>    <td>{client_host}</td>  </tr>
<tr>  <td>Client port</td>    <td>{client_port}s</td> </tr>
<tr>  <td>Command</td>        <td>{command}</td>      </tr>
<tr>  <td>Path</td>           <td>{path}</td>         </tr>
</table>
</body>
</html>
"""

ERROR_PAGE = """\
<html>
<body>
<h1>Error accessing {path}</h1>
<p>{msg}</p>
</body>
</html>    
"""

DIRECTORY_LISTING = """\
<html>
<body>
<h1>LISTING OF DIRECTORY: {path}</h1>
<ul>
{items}
</ul>
</body>
</html>    
"""

class ServerException(Exception):
    """Custom exception for server errors."""
    pass

class base_case(object):
    '''Parent for case handlers'''

    def handle_file(self, handler):
        try:
            with open(handler.full_path, 'r') as reader:
                content = reader.read()
            handler.send_content(content)
        # FILE CANNOT BE READ
        except IOError as msg:
            msg = "'{0}' cannot be read: {1}".format(handler.full_path, msg)
            handler.handle_error(msg)
    
    # Constructs index.html file path
    def index_path(self, handler):
        return os.path.join(handler.full_path, 'index.html')
    def test(self, handler):
        assert False, 'Not implemented.'
    def act(self, handler):
        assert False,'Not implemented.'
        
class case_no_file(base_case):
    '''File or directory does not exist.'''

    def test(self, handler):
        return not os.path.exists(handler.full_path)
    
    def act(self, handler):
        raise ServerException("'{0}' not found".format(handler.path)) 

class case_existing_file(base_case):
    '''File exists.'''

    def test(self, handler):
        return os.path.isfile(handler.full_path)
    def act(self, handler):
        self.handle_file(handler)

class case_directory_index_file(base_case):
    '''Path provided is a directory and index.html file exists'''
    def test(self, handler):
        if os.path.isdir(handler.full_path): 
            return os.path.isfile(os.path.join(handler.full_path, "index.html"))
    def act(self, handler):
        handler.full_path += "/index.html"
        self.handle_file(handler)
class case_directory_no_index_file(base_case):
    def test(self, handler):
        return not os.path.isfile(os.path.join(handler.full_path, "index.html"))
    def act(self, handler):
        visible_items = [item for item in os.listdir(handler.full_path) if not item.startswith(".")]
        self.send_dir_listing_html(handler, visible_items)
    def send_dir_listing_html(self, handler, visible_items):
        list_items = "\n".join(f"<li>{item}</li>" for item in visible_items)
        html_content = DIRECTORY_LISTING.format(path=handler.full_path, items=list_items)
        handler.send_content(html_content)

class RequestHandler(http.server.BaseHTTPRequestHandler):
    Cases = [case_no_file(),
             case_existing_file(),
             case_directory_index_file(),
             case_directory_no_index_file()]

    # Classify and Handle Request.
    def do_GET(self):
        try:
            # Figure out what exactly is being requested.
            self.full_path = os.getcwd() + self.path

            # Figure out how to handle it.
            for case in self.Cases:
                if case.test(self):
                    case.act(self)
                    break
        # Handle errors.
        except Exception as msg:
            self.handle_error(msg)

    # Handle unknown objects.
    def handle_error(self, msg):
        content = ERROR_PAGE.format(path=self.path, msg=msg)
        self.send_content(content, 404)

    
    # Send actual content.
    def send_content(self, content, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        content = content.encode('utf-8')
        self.wfile.write(content)

if __name__ == '__main__':
    serverAddress = ('', 8080)
    server = http.server.HTTPServer(serverAddress, RequestHandler)
    server.serve_forever()