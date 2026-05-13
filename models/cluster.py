from services.qualityAnalyse_service import QualityAnalyseService


class Cluster:
    def __init__(self, id, name, create_time, session_id,
                 size=None, silhouette=None, cohesion=None, separation=None,
                 density=None, radius=None):
        self. id = id
        self.name = name
        self.create_time = create_time
        self.size = size
        self.silhouette = silhouette
        self.cohesion = cohesion
        self.separation = separation
        self.density = density
        self.radius = radius
        self.session_id = session_id
        self.images_list = []
        self.count_images = 0

    def set_quality_params(self, params):
        self.size = params['size']
        self.silhouette = params['silhouette']
        self.cohesion = params['cohesion']
        self.separation = params['separation']
        self.density = params['density']
        self.radius = params['radius']

    #создание кластера из строки БД
    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id = row['id'],
            name = row['name'],
            create_time = row['create_time'],
            silhouette = row['silhouette'],
            size=row['size'],
            cohesion=row['cohesion'],
            separation=row['separation'],
            density=row['density'],
            radius=row['radius'],
            session_id=row['session_id']
        )