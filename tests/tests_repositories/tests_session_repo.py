def test_create_session(session_repo, dataset_repo):
    # создаём датасет
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    # сессия кластеризации
    session = session_repo.create_session("TestSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    assert session.name == "TestSession"
    assert session.algorythm == "DBSCAN"
    assert session.params["eps"] == 0.5
    assert session.dataset_id == dataset.id

def test_count_existingSessions(dataset_repo, session_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    first_session = session_repo.create_session("FirstSession",
                                          {"algorythm": "DBSCAN", "eps": 0.5},
                                          dataset.id)
    second_session = session_repo.create_session("SecondSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)
    third_session = session_repo.create_session("ThirdSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)
    count = session_repo.count_existingSessions(dataset.id)
    assert count == 3

def test_get_session_by_name(dataset_repo, session_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    first_session = session_repo.create_session("FirstSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)
    second_session = session_repo.create_session("SecondSession",
                                                 {"algorythm": "DBSCAN", "eps": 0.5},
                                                 dataset.id)
    found_first = session_repo.get_session_by_name("FirstSession", dataset.id)
    assert found_first.id == first_session.id

def test_get_sessions_by_dataset(dataset_repo, session_repo):
    dataset = dataset_repo.create_dataset("Dataset1", "/path", 1)
    dataset2 = dataset_repo.create_dataset("Dataset2", "/path2", 1)
    first_session = session_repo.create_session("FirstSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)
    second_session = session_repo.create_session("SecondSession",
                                                 {"algorythm": "DBSCAN", "eps": 0.5},
                                                 dataset2.id)
    third_session = session_repo.create_session("ThirdSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)
    found_sessions = session_repo.get_sessions_by_dataset(dataset.id)
    assert len(found_sessions) == 2
    assert found_sessions[0].id == first_session.id
    assert found_sessions[1].id == third_session.id

def test_change_name(session_repo, dataset_repo):
    dataset = dataset_repo.create_dataset("ChangeCluster", "/path", 1)
    first_session = session_repo.create_session("FirstSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)
    session_repo.change_name("NewName", first_session.id)
    session_changed = session_repo.get_sessions_by_dataset(dataset.id)[0]

    assert session_changed.id == first_session.id
    assert session_changed.name == "NewName"

def test_delete_sessions(session_repo, dataset_repo):
    dataset = dataset_repo.create_dataset("Dataset", "/path2", 1)
    first_session = session_repo.create_session("FirstSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)
    second_session = session_repo.create_session("SecondSession",
                                                 {"algorythm": "DBSCAN", "eps": 0.5},
                                                 dataset.id)
    third_session = session_repo.create_session("ThirdSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)
    session_repo.delete_sessions([first_session.id, third_session.id])

    found_sessions = session_repo.get_sessions_by_dataset(dataset.id)

def test_save_quality_params(session_repo, dataset_repo):
    dataset = dataset_repo.create_dataset("Dataset", "/path2", 1)
    first_session = session_repo.create_session("FirstSession",
                                                {"algorythm": "DBSCAN", "eps": 0.5},
                                                dataset.id)

    params = {"silhouette": 0.5,
            "chi": 0.3,
            "dbi": 0.4}
    session_repo.save_quality_params(params, first_session.id)

    found_session = session_repo.get_session_by_name("FirstSession", dataset.id)

    assert found_session.silhouette == 0.5
    assert found_session.DBI_index == 0.4
    assert found_session.CHI_index == 0.3