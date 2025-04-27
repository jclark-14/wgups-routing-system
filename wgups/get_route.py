
_distance_matrix = []
_address_map = {}

def init_distance_data(matrix, addr_map):
    global _distance_matrix, _address_map
    _distance_matrix = matrix
    _address_map = addr_map

def get_distance(from_addr: str, to_addr: str) -> float:
    idx1 = _address_map[from_addr]
    idx2 = _address_map[to_addr]
    return _distance_matrix[idx1][idx2]