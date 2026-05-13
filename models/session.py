import json


class Session:
    def __init__(self, id, name, algorytm, params, dataset_id, created_at=None,
                 silhouette=None, CHI_index=None, DBI_index = None):
        self.id = id
        self.name = name
        self.algorythm = algorytm
        self.params = params
        self.dataset_id = dataset_id
        self.silhouette = silhouette
        self.CHI_index = CHI_index
        self.DBI_index = DBI_index
        self.created_at = created_at
        self.clusters_list = []
        self.anomaly_group = None

    def set_quality_params(self, params):
        self.silhouette = params['silhouette']
        self.DBI_index = params['dbi']
        self.CHI_index = params['chi']

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        params = json.loads(row['parameters'])
        return cls(
            id = row['id'],
            name = row['name'],
            algorytm=row['algorythm'],
            params=params,
            dataset_id=row['dataset_id'],
            silhouette=row['silhouette'],
            CHI_index=row['chi_index'],
            DBI_index=row['dbi_index'],
            created_at = row['created_at']
        )
