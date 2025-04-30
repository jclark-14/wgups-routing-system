class HashTable:
    """
    Custom hash table for efficient package storage and retrieval.

    Space complexity: O(n), where n is the number of packages.
    Time complexity (average case): O(1) for insert, lookup, and delete.
    """

    def __init__(self, size=40):
        """
        Initialize hash table with empty buckets.
        
        Args:
            size (int): Number of buckets. Default is 40 for package IDs 1–40.
        """
        self.size = size
        self.table = [[] for _ in range(size)]

    def _hash(self, key):
        """Hash function using modulo to determine bucket index."""
        return key % self.size

    def insert(self, key, value):
        """
        Insert or update a key-value pair.

        Args:
            key (int): Package ID
            value (Package): Package object
        """
        hash_index = self._hash(key)

        for i, item in enumerate(self.table[hash_index]):
            if item[0] == key:
                self.table[hash_index][i] = (key, value)
                return

        self.table[hash_index].append((key, value))

    def lookup(self, key):
        """
        Retrieve a value by key.

        Args:
            key (int): Package ID

        Returns:
            Package: The corresponding package, or None if not found.
        """
        hash_index = self._hash(key)

        for item in self.table[hash_index]:
            if item[0] == key:
                return item[1]

        return None

    def delete(self, key):
        """Remove a key-value pair, if it exists."""
        hash_index = self._hash(key)

        for i, item in enumerate(self.table[hash_index]):
            if item[0] == key:
                del self.table[hash_index][i]
                return

    def __iter__(self):
        """Iterate through all stored keys."""
        for bucket in self.table:
            for key, _ in bucket:
                yield key

    def items(self):
        """Return all key-value pairs."""
        return [item for bucket in self.table for item in bucket]

    def __len__(self):
        """Return the total number of items in the table."""
        return sum(len(bucket) for bucket in self.table)

    def __repr__(self):
        """String representation showing contents summary."""
        keys = list(self)
        return f"<HashTable: {len(self)} packages | Keys: {keys}>"
