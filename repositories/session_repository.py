import json

from models.session import Session

class SessionRepository:
    def __init__(self, conn):
        self.conn = conn

    def save_quality_params(self, params, session_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """UPDATE sessions SET
                silhouette = ?,
                chi_index =?,
                dbi_index = ?
                WHERE id = ?""",
            (params['silhouette'], params['chi'], params['dbi'], session_id))
        self.conn.commit()

    def delete_sessions(self, session_ids):
        cursor = self.conn.cursor()
        placeholders = ','.join('?' * len(session_ids))
        query = f"DELETE FROM sessions WHERE id IN ({placeholders})"
        cursor.execute(query, session_ids)
        self.conn.commit()


    def change_name(self, new_name, session_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE sessions SET name = ? WHERE id = ?",
                       (new_name, session_id))
        self.conn.commit()

    def create_session(self, name, params, dataset_id):
        cursor = self.conn.cursor()

        algorythm = params['algorythm']
        del params['algorythm']

        params_json = json.dumps(params, ensure_ascii=False, indent=2)

        cursor.execute(
            "INSERT INTO sessions (name, algorythm, parameters, dataset_id) VALUES (?, ?, ?, ?)",
            (name, algorythm, params_json, dataset_id)
        )
        self.conn.commit()

        return self.get_session_by_name(name, dataset_id)

    def get_sessions_by_dataset(self, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE dataset_id = ?;",
            (dataset_id,)
        )
        rows = cursor.fetchall()
        if rows is None:
            return None

        sessions = []
        for row in rows:
            loaded_session = Session.from_row(row)
            sessions.append(loaded_session)

        return sessions

    def get_session_by_name(self, name, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE name = ? AND dataset_id = ?;",
            (name, dataset_id)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Session.from_row(row)


    def count_existingSessions(self, dataset_id):
        cursor = self.conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM sessions WHERE dataset_id = ?",
                       (dataset_id,))
        count = cursor.fetchone()[0]

        return count