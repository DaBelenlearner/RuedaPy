import json
import networkx as nx
import matplotlib.pyplot as plt

# Load the moves JSON data
with open("moves.json", "r") as f:
    moves = json.load(f)

# Create a directed graph
G = nx.DiGraph()

# Add nodes (moves)
for move_key, move_data in moves.items():
    G.add_node(move_key, label=move_data["called_name"])

# Add edges based on allowed transitions
for from_key, from_data in moves.items():
    for to_key, to_data in moves.items():
        if from_key == to_key:
            continue
        if from_data["postcondition"] != to_data["precondition"]:
            continue
        if "requires" in to_data and from_key not in to_data["requires"]:
            continue
        if "must_be_followed_by" in from_data and to_key not in from_data["must_be_followed_by"]:
            continue
        G.add_edge(from_key, to_key)

# Draw the graph with improved arrow visibility
plt.figure(figsize=(14, 10))
pos = nx.spring_layout(G, seed=42)

# Draw nodes and labels
nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="lightblue", edgecolors='black')
nx.draw_networkx_labels(G, pos, labels={n: moves[n]["called_name"] for n in G.nodes}, font_size=9)

# Draw edges with curved arrows to improve visibility
nx.draw_networkx_edges(
    G,
    pos,
    arrowstyle='-|>',
    arrowsize=20,
    edge_color='gray',
    connectionstyle='arc3,rad=0.1'  # adds curve to avoid overlap
)

plt.title("Rueda Move Transition Graph", fontsize=14)
plt.axis("off")
plt.tight_layout()
plt.show()
