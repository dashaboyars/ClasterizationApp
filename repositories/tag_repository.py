from models.tag import Tag

class TagRepository:
    def __init__(self, conn):
        self.conn = conn

    def get_tags_by_image(self, image_id, dataset_id):
        cursor = self.conn.cursor()
        cursor.execute(
            """SELECT t.* 
            FROM tags t
            JOIN images_tags it ON t.id = it.tag_id
            JOIN images_datasets imd ON imd.id = it.image_in_dataset_id
            WHERE imd.image_id = ? AND imd.dataset_id = ?""",
            (image_id, dataset_id))
        rows = cursor.fetchall()
        tags = []
        for row in rows:
            tags.append(Tag.from_row(row))
        return tags

    def set_tag_toImages(self, tag_id, images_ids):
        cursor = self.conn.cursor()
        all_values = [(img_id, tag_id) for img_id in images_ids]
        cursor.executemany("""
                INSERT INTO images_tags (image_in_dataset_id, tag_id)
                VALUES (?, ?)""",
                all_values)
        self.conn.commit()

    def create_tag(self, name):
        exists = self.get_tag_by_name(name)
        if exists:
            return exists

        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO tags (name) VALUES (?)",
            (name,)
        )
        self.conn.commit()
        return self.get_tag_by_name(name)


    def get_tag_by_name(self, name):
        cursor = self.conn.cursor()

        cursor.execute(
            "SELECT * FROM tags WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return Tag.from_row(row)
