from models.anomaly_group import AnomalyGroup

class AnomalyGroupRepository():
    def __init__(self, conn):
        self.conn = conn

    def delete_group(self, anomalyGroup_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM anomaliesGroups WHERE id = ?",
                       (anomalyGroup_id, ))
        self.conn.commit()

    def get_anomalyGroup_by_session(self, session_id):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM anomaliesGroups WHERE session_id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return AnomalyGroup.from_row(row)

    def add_image_to_group(self, image_id, group_id):
        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO images_anomalies (image_id, anomaliesGroup_id) VALUES (?, ?)",
            (image_id, group_id))
        self.conn.commit()

    def create_group(self, name, session_id):
        cursor = self.conn.cursor()

        cursor.execute(
            "INSERT INTO anomaliesGroups (name, session_id) VALUES (?, ?)",
            (name, session_id)
        )
        self.conn.commit()

        return self.get_group_by_name(name, session_id)

    def get_group_by_name(self, name, session_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM anomaliesGroups WHERE name = ? AND session_id = ?;",
            (name, session_id)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return AnomalyGroup.from_row(row)