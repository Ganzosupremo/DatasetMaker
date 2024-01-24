class Event:
    def __init__(self) -> None:
        self.subscribers = []
        
    def subscribe(self, callback):
        self.subscribers.append(callback)
    
    
    def emit(self, text):
        for callback in self.subscribers:
            callback(text)