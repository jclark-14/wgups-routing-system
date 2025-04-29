class HashTable:
    """
    Custom hash table implementation for efficient package storage and retrieval.
    
    Space complexity: O(n) where n is the number of packages
    Time complexity: O(1) average for insert, lookup, and delete operations
    """
    
    def __init__(self, size=40):
        """Initialize hash table with specified size (default 40 for packages)."""
        self.size = size
        self.table = [[] for _ in range(size)]
    
    def _hash(self, key):
        """Hash function that maps package ID to bucket index."""
        return key % self.size
    
    def insert(self, key, value):
        """
        Insert or update a key-value pair in the hash table.
        
        Args:
            key: The package ID (integer)
            value: The package object
        """
        hash_index = self._hash(key)
        
        # Check if key already exists
        for i, item in enumerate(self.table[hash_index]):
            if item[0] == key:
                self.table[hash_index][i] = (key, value)
                return
                
        # If key doesn't exist, append to bucket
        self.table[hash_index].append((key, value))
    
    def lookup(self, key):
        """
        Look up a package by ID and return its object.
        
        Args:
            key: The package ID to look up
            
        Returns:
            Package object if found, None otherwise
        """
        hash_index = self._hash(key)
        
        for item in self.table[hash_index]:
            if item[0] == key:
                return item[1]
                
        return None
    
    def delete(self, key):
        """Remove a key-value pair from the hash table."""
        hash_index = self._hash(key)
        
        for i, item in enumerate(self.table[hash_index]):
            if item[0] == key:
                del self.table[hash_index][i]
                return
    
    def __iter__(self):
        """Make hash table iterable to get all package IDs."""
        for bucket in self.table:
            for key, _ in bucket:
                yield key
                
    def items(self):
        """Return all key-value pairs in the hash table."""
        items = []
        for bucket in self.table:
            for item in bucket:
                items.append(item)
        return items
        
    def __len__(self):
        """Return the total number of packages in the hash table."""
        total = 0
        for bucket in self.table:
            total += len(bucket)
        return total
    
    def __repr__(self):
        keys = list(self)
        return f"<HashTable: {len(self)} packages | Keys: {keys}>"
