from models.cluster import Cluster

class ClusterRepository:
    def __init__(self, conn):
        self.conn = conn

    def save_params(self, params, cluster_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE clusters SET 
            size = ?, 
            cohesion = ?, 
            separation = ?, 
            density = ?,
            radius = ?,
            silhouette = ?
            WHERE id = ?""",
            (params['size'], params['cohesion'], params['separation'], params['density'],
             params['radius'], params['silhouette'], cluster_id)
        )
        self.conn.commit()

    def save_silhouette(self, silhouette, cluster_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE clusters SET silhouette = ? WHERE id = ?""",
            (silhouette, cluster_id))
        self.conn.commit()

    def delete_cluster(self, cluster_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "DELETE FROM clusters WHERE id = ?",
            (cluster_id,)
        )
        self.conn.commit()

    def rename_cluster(self, new_name, cluster_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE clusters SET name = ? WHERE id = ?",
            (new_name, cluster_id)
        )
        self.conn.commit()

    def add_image_to_cluster(self, image_id, cluster_id, manual):
        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO images_clusters (image_id, cluster_id, manual) VALUES (?, ?, ?)",
            (image_id, cluster_id, manual)
        )
        self.conn.commit()

    def get_clusters_by_session(self, session_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM clusters WHERE session_id = ?;",
            (session_id,)
        )
        rows = cursor.fetchall()
        if rows is None:
            return None

        clusters=[]
        for row in rows:
            loaded_cluster = Cluster.from_row(row)
            clusters.append(loaded_cluster)

        return clusters

    def create_cluster(self, name, session_id):
        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO clusters (name, session_id) VALUES (?, ?)",
            (name, session_id)
        )
        self.conn.commit()

        return self.get_cluster_by_name(name, session_id)

    def get_cluster_by_name(self, name, session_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM clusters WHERE name = ? AND session_id = ?;",
            (name, session_id)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Cluster.from_row(row)


