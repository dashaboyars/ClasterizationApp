import numpy as np


def test_get_tags_by_image(tag_repo, image_repo, dataset_repo):
    dataset = dataset_repo.create_dataset("TestDataset", "/path", user_id=1)
    embedding = np.zeros(1280, dtype=np.float32)
    image = image_repo.create_image("TestImage", "/TestImage",
                                    ".jpg", dataset.id, embedding)

    tag1 = tag_repo.create_tag("first_tag")
    tag2 = tag_repo.create_tag("second_tag")
    pair_id = image_repo.get_imageDataset_Pair_Ids([image.id], dataset.id)
    tag_repo.set_tag_toImages(tag1.id, pair_id)
    tag_repo.set_tag_toImages(tag2.id, pair_id)

    tags = tag_repo.get_tags_by_image(image.id, dataset.id)
    assert tags[0].name == "first_tag" or tags[0].name == "second_tag"
    assert tags[1].name == "first_tag" or tags[1].name == "second_tag"

def test_get_tag_by_name(tag_repo):
    tag1 = tag_repo.create_tag("first_tag")

    tag_found = tag_repo.get_tag_by_name("first_tag")
    assert tag1.id == tag_found.id

def test_create_tag_exists(tag_repo):
    tag1 = tag_repo.create_tag("first_tag")

    tag_exists = tag_repo.create_tag("first_tag")
    assert tag_exists is not None
    assert tag_exists.id == tag1.id

