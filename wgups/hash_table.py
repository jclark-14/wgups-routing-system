from typing import Any, List, Optional, Tuple

class HashTable: 
    """Generic hash table with chaining for collision handling"""
    
    def __init__(self, capacity: int = 97):
        self.capacity = capacity
        self.table: List[List[Tuple[int, Any]]] = [[] for _ in range(capacity)]
        self.size = 0
    
    def _hash(self, key: int) -> int:
        # Simple hashing for unique keys
        return key % self.capacity
        
    def insert(self, key: int, value: Any) -> None:
        """Insert/update key-value pair"""
        idx = self._hash(key)
        # If key exists -> update
        for i, (k, _) in enumerate(self.table[idx]):
            if k == key:
                self.table[idx][i] = (key, value)
                return
        # If key doesn't exist -> insert
        self.table[idx].append((key, value))
        self.size += 1
         
    def lookup(self, key: int) -> Optional[Any]:
        """Look up by key"""
        idx = self._hash(key)
        # If key exists -> return value
        for k, v in self.table[idx]:
            if k == key:
                return v
        return None
            
    def remove(self, key: int) -> bool:
        """Remove key-value pair"""
        idx = self._hash(key)
        # If key found -> remove
        for i, (k, _) in enumerate(self.table[idx]):
            if k == key: 
                self.table[idx].pop(i)
                self.size -= 1
                return True
        return False
    
    def keys(self) -> List[int]:
        """Get all keys in hash table"""
        keys = []
        for bucket in self.table: 
            for k, _ in bucket:
                keys.append(k)
        return keys
    
    def __contains__(self, key:int) -> bool:
        # Enables "in" functionality
        idx = self._hash(key)
        return any(k == key for k, _ in self.table[idx])

    def __iter__(self):
        # Enables key iteration
        for bucket in self.table:
            for k, _ in bucket: 
                yield k
    
    def items (self):
        # Enables key-value pair iteration
        for bucket in self.table:
            for k, v in bucket:
                yield(k, v)
        
    def __len__(self) -> int:
        return self.size
    
    def __str__(self) -> str:
        # Print Hashtable capacity and size
        return f"HashTable(Capcity: {self.capacity}, Size: {self.size})"
    
    def debug(self) -> None:
        # Print all buckets for debugging
        print(f"HashTable Debug - Capacity: {self.capacity}, Size: {self.size}")
        for i, bucket in enumerate(self.table):
            if bucket:
                print(f"   Bucket {i}: {bucket}")