import numpy as np


def test_create_cluster(session_repo, dataset_repo,cluster_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster1", session.id)
    assert cluster.name == "Cluster1"
    assert cluster.session_id == session.id

def test_get_clusters_by_session(dataset_repo, session_repo, cluster_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    other_session = session_repo.create_session("OtherSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    cluster1 = cluster_repo.create_cluster("Cluster1", session.id)
    cluster2 = cluster_repo.create_cluster("Cluster2", session.id)
    cluster3 = cluster_repo.create_cluster("Cluster3", other_session.id)
    found_clusters = cluster_repo.get_clusters_by_session(session.id)
    clus_ids = [cl.id for cl in found_clusters]
    assert cluster1.id in clus_ids
    assert cluster2.id in clus_ids
    assert cluster3.id not in clus_ids

def test_add_image_to_cluster(dataset_repo, session_repo, cluster_repo, image_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster1", session.id)
    embedding = np.zeros(1280, dtype=np.float32)
    img = image_repo.create_image("img.jpg", "/path", "jpg", dataset.id, embedding, None)
    cluster_repo.add_image_to_cluster(img.id, cluster.id, True)
    images = image_repo.get_images_by_cluster(cluster.id, dataset.id)

    assert len(images) == 1
    assert images[0].id == img.id

def test_rename_cluster(dataset_repo, session_repo, cluster_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster1", session.id)
    cluster_repo.rename_cluster("NewName", cluster.id)
    changed_cluster = cluster_repo.get_cluster_by_name("NewName", session.id)

    assert changed_cluster is not None
    assert changed_cluster.id == cluster.id
    assert changed_cluster.name == "NewName"

def test_delete_cluster(dataset_repo, session_repo, cluster_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster1", session.id)
    cluster_repo.delete_cluster(cluster.id)
    found_clusters = cluster_repo.get_clusters_by_session(session.id)
    assert found_clusters is not None
    assert len(found_clusters) == 0

def test_save_silhouette(dataset_repo, session_repo, cluster_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster1", session.id)
    cluster_repo.save_silhouette(0.9, cluster.id)
    cluster_saved_silhouette = cluster_repo.get_cluster_by_name("Cluster1", session.id)
    assert cluster_saved_silhouette is not None
    assert cluster_saved_silhouette.silhouette == 0.9

def test_save_params(dataset_repo, session_repo, cluster_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    cluster = cluster_repo.create_cluster("Cluster1", session.id)
    params = {
        'size': 0,
        'cohesion': 0.4,
        'separation': 0.5,
        'density': 0.1,
        'radius': 0.8,
        'silhouette': 0.2
    }
    cluster_repo.save_params(params, cluster.id)
    updated_cluster = cluster_repo.get_cluster_by_name("Cluster1", session.id)

    assert updated_cluster.size == 0
    assert updated_cluster.cohesion == 0.4
    assert updated_cluster.separation == 0.5
    assert updated_cluster.density == 0.1
    assert updated_cluster.radius == 0.8
    assert updated_cluster.silhouette == 0.2

