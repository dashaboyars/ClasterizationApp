def test_save_new_version(modelVersion_repo):
    new_model = modelVersion_repo.save_new_version("path", ["label1", "label2"], "new_model")
    assert new_model.name == "new_model"
    assert new_model.onnx_path == "path"
    assert new_model.is_active == False
    assert new_model.label_map[0] == "label1"
    assert new_model.label_map[1] == "label2"

def test_load_all_versions(modelVersion_repo):
    first_model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "first_model")
    second_model = modelVersion_repo.save_new_version("path2", ["label2", "label3"], "second_model")
    all_versions = modelVersion_repo.load_all_versions()

    found_ids = [model.id for model in all_versions]
    assert first_model.id in found_ids
    assert second_model.id in found_ids

def test_change_active_version(modelVersion_repo):
    first_model = modelVersion_repo.save_new_version("path1", ["label1", "label2"], "first_model")
    modelVersion_repo.change_active_version("first_model")
    all_versions = modelVersion_repo.load_all_versions()

    count_active = 0
    for model in all_versions:
        if model.is_active:
            count_active += 1

    active_model = [model for model in all_versions if model.is_active][0]

    assert count_active == 1
    assert active_model.id == first_model.id

