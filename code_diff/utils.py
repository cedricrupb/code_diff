
def cached_property(fnc):
    name = fnc.__name__

    def load_from_cache(self):
        if not hasattr(self, "_cache"): self._cache = {}

        if name not in self._cache:
            self._cache[name] = fnc(self)
        
        return self._cache[name]
    
    return property(load_from_cache)