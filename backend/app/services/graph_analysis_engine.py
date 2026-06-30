from typing import Dict, List, Set, Any

class GraphAnalysisEngine:
    """
    Graph-Based Dependency Analysis Engine for SentinelNet AI.
    Builds the network topology graph and computes paths, blast radii,
    critical nodes, and single points of failure (SPOF).
    """

    def __init__(self):
        # Topology definitions
        # Nodes: DC-Bangalore, HUB-Mumbai, BR-Delhi, BR-Kolkata, BR-Chennai, BR-Hyderabad
        self.nodes = {
            "DC-Bangalore": {"name": "Bangalore DC (Core)", "type": "DC", "users": 1500, "criticality": 1.0},
            "HUB-Mumbai": {"name": "Mumbai Hub (Transit)", "type": "Hub", "users": 800, "criticality": 0.9},
            "BR-Delhi": {"name": "New Delhi Branch (BR-1)", "type": "Branch", "users": 250, "criticality": 0.6},
            "BR-Kolkata": {"name": "Kolkata Branch (BR-2)", "type": "Branch", "users": 180, "criticality": 0.5},
            "BR-Chennai": {"name": "Chennai Branch (BR-3)", "type": "Branch", "users": 300, "criticality": 0.7},
            "BR-Hyderabad": {"name": "Hyderabad Branch (BR-4)", "type": "Branch", "users": 220, "criticality": 0.6}
        }
        
        # Adjacency list representation (Undirected graph of primary paths)
        self.graph: Dict[str, Set[str]] = {
            "DC-Bangalore": {"HUB-Mumbai"},
            "HUB-Mumbai": {"DC-Bangalore", "BR-Delhi", "BR-Kolkata", "BR-Chennai", "BR-Hyderabad"},
            "BR-Delhi": {"HUB-Mumbai"},
            "BR-Kolkata": {"HUB-Mumbai"},
            "BR-Chennai": {"HUB-Mumbai"},
            "BR-Hyderabad": {"HUB-Mumbai"}
        }

    def get_dependency_path(self, source: str, target: str) -> List[str]:
        """
        Calculates the dependency path between two nodes using BFS.
        """
        if source not in self.graph or target not in self.graph:
            return []
            
        visited = {source}
        queue = [[source]]
        
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == target:
                return path
                
            for neighbor in self.graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    queue.append(new_path)
        return []

    def analyze_node_failure(self, failed_node: str) -> Dict[str, Any]:
        """
        Simulates a node failure to calculate dynamic blast radius,
        downstream impacts, affected branches, users, and services.
        """
        if failed_node not in self.nodes:
            return {
                "blast_radius": 0.0,
                "affected_branches": [],
                "affected_users": 0,
                "affected_services": [],
                "is_spof": False,
                "criticality_score": 0.0
            }

        # Build list of active nodes after failure
        active_nodes = set(self.nodes.keys()) - {failed_node}
        
        # Determine reachability to DC-Bangalore for all remaining nodes
        reachable_to_dc = set()
        if "DC-Bangalore" in active_nodes:
            reachable_to_dc.add("DC-Bangalore")
            # Run BFS to find all nodes that can still reach DC
            queue = ["DC-Bangalore"]
            visited = {"DC-Bangalore", failed_node} # mark failed as visited
            while queue:
                curr = queue.pop(0)
                for neighbor in self.graph[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        reachable_to_dc.add(neighbor)
                        queue.append(neighbor)

        # Disconnected/impacted nodes are those that cannot reach the core DC (or the failed node itself)
        impacted_nodes = set(self.nodes.keys()) - reachable_to_dc
        
        # Blast Radius is percentage of network nodes impacted
        total_nodes = len(self.nodes)
        blast_radius = (len(impacted_nodes) / total_nodes) * 100.0

        # Calculate affected branches and users
        affected_branches = []
        affected_users = self.nodes[failed_node]["users"]
        affected_services = []

        for node_id in impacted_nodes:
            if node_id != failed_node:
                node_info = self.nodes[node_id]
                affected_users += node_info["users"]
                if node_info["type"] == "Branch":
                    affected_branches.append(node_id)

        # Determine services impacted based on node type
        if failed_node == "DC-Bangalore":
            affected_services = ["Intranet Replication", "Central Database Sync", "Enterprise Active Directory", "VoIP Core Server"]
        elif failed_node == "HUB-Mumbai":
            affected_services = ["Transit Overlay Routing", "MPLS Hub Gateway", "VoIP Trunk Relay"]
        else:
            affected_services = [f"{failed_node} Local Subnet Routing", "VoIP Branch Queue"]

        # An active transit node is a Single Point of Failure (SPOF) if its removal disconnects other nodes
        is_spof = False
        if failed_node == "HUB-Mumbai":
            is_spof = True

        criticality_score = self.nodes[failed_node]["criticality"]

        return {
            "blast_radius": round(blast_radius, 2),
            "affected_branches": affected_branches,
            "affected_users": affected_users,
            "affected_services": affected_services,
            "is_spof": is_spof,
            "criticality_score": criticality_score
        }

    def get_critical_nodes(self) -> List[str]:
        """
        Returns nodes prioritized by their topological criticality and user impact.
        """
        return sorted(self.nodes.keys(), key=lambda x: self.nodes[x]["criticality"], reverse=True)

# Singleton Instance
graph_analysis_engine = GraphAnalysisEngine()
