import json


class ClasificationSession:
    def __init__(self, id, name, model_id, dataset_id, created_at=None):
        self.id = id
        self.name = name
        self.model_id = model_id
        self.dataset_id = dataset_id
        self.images_labels = {}
        self.created_at = created_at

    def create_images_labels_dict(self, labels):
        self.images_labels = {}
        for label in labels:
            self.images_labels[label] = []


    def get_avg_confidence(self):
        conf_sum = 0
        count_items = 0
        for group in self.images_labels.values():
            if group is None:
                continue
            conf_sum += sum([item[1] for item in group])
            count_items += len(group)
        if count_items == 0:
            return 0
        avg_conf = round(conf_sum/count_items, 2)
        return avg_conf

    def get_avg_confidence_byGroup(self, group_name):
        group = self.images_labels[group_name]
        if len(group) == 0:
            return 0
        avg_conf = sum([item[1] for item in group])/len(group)
        return round(avg_conf, 2)

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id =row['id'],
            name=row['name'],
            model_id=row['model_version_id'],
            dataset_id=row['dataset_id'],
            created_at=row['created_at']
        )