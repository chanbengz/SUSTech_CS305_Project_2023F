import socket, selectors
from time import monotonic as time
from threading import Thread, Event

class Server:
    class _Threads(list):
        def append(self, thread):
            self.reap()
            if thread.daemon:
                return
            super().append(thread)
        def pop_all(self):
            self[:], result = [], self[:]
            return result
        def join(self):
            for thread in self.pop_all():
                thread.join()
        def reap(self):
            self[:] = (thread for thread in self if thread.is_alive())
    
    timeout = None       
    _threads = _Threads()
    selector = selectors.PollSelector()

    def __init__(self, server_address, RequestHandler):
        self.server_address = server_address
        self.RequestHandler = RequestHandler
        self.__is_shut_down = Event()
        self.__shutdown_request = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            self.socket.bind(self.server_address)
            self.server_address = self.socket.getsockname()
            self.socket.listen(10) # Allow the maximum Concurrent
        except:
            self.server_close()
            raise

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        t = Thread(target = self.process_request_thread, args = (request, client_address))
        t.daemon = False
        self._threads.append(t)
        t.start()

    def server_close(self):
        self.socket.close()
        self._threads.join()

    def shutdown_request(self, request):
        try:
            request.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        self.close_request(request)

    def close_request(self, request):
        request.close()

    def serve_forever(self, poll_interval=0.5):
        self.__is_shut_down.clear()
        try:
            self.selector.register(self, selectors.EVENT_READ)
            while not self.__shutdown_request:
                ready = self.selector.select(poll_interval)
                if self.__shutdown_request:
                    break
                if ready:
                    self._handle_request_noblock()
        finally:
            self.__shutdown_request = False
            self.__is_shut_down.set()

    def shutdown(self):
        self.__shutdown_request = True
        self.__is_shut_down.wait()

    def fileno(self):
        return self.socket.fileno()
    
    def handle_request(self):
        timeout = self.socket.gettimeout()
        if timeout is None:
            timeout = self.timeout
        elif self.timeout is not None:
            timeout = min(timeout, self.timeout)
        if timeout is not None:
            deadline = time() + timeout

        self.selector.register(self, selectors.EVENT_READ)
        while True:
            if self.selector.select(timeout):
                return self._handle_request_noblock()
            else:
                if timeout is not None:
                    timeout = deadline - time()
                    if timeout < 0:
                        return self.handle_timeout()

    def _handle_request_noblock(self):
        try:
            request, client_address = self.socket.accept()
        except OSError:
            return
        try:
            self.process_request(request, client_address)
        except Exception:
            self.shutdown_request(request)

    def process_request(self, request, client_address):
        self.finish_request(request, client_address)
        self.shutdown_request(request)

    def finish_request(self, request, client_address):
        self.RequestHandler(request, client_address, self)

    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.server_close()