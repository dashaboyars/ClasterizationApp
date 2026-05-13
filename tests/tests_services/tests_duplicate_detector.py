import numpy as np


def test_find_duplicates_no_duplicates(duplicate_detector, mock_dataset, mock_image):
    # Создаём уникальные эмбеддинги (ортогональные, косинусное расстояние ~0)
    emb1 = np.array([1.0, 0.0, 0.0])
    emb2 = np.array([0.0, 1.0, 0.0])
    emb3 = np.array([0.0, 0.0, 1.0])
    img1 = mock_image(1, emb1)
    img2 = mock_image(2, emb2)
    img3 = mock_image(3, emb3)
    dataset = mock_dataset([img1, img2, img3])
    threshold = 0.95

    result = duplicate_detector.find_duplicates(dataset, progress_callback=None, cancel_check=None, threshold=threshold)
    duplicate_groups, returned_dataset = result
    assert duplicate_groups == []
    assert returned_dataset is dataset


def test_find_duplicates_with_one_pair(duplicate_detector, mock_dataset, mock_image):
    # Создаём два одинаковых эмбеддинга и один другой
    emb1 = np.array([1.0, 0.0])
    emb2 = np.array([1.0, 0.0])  # идентичен emb1
    emb3 = np.array([0.0, 1.0])
    img1 = mock_image(1, emb1)
    img2 = mock_image(2, emb2)
    img3 = mock_image(3, emb3)
    dataset = mock_dataset([img1, img2, img3])
    threshold = 0.99  # косинусное сходство двух одинаковых векторов = 1.0

    result = duplicate_detector.find_duplicates(dataset, progress_callback=None, cancel_check=None, threshold=threshold)
    duplicate_groups, _ = result
    assert len(duplicate_groups) == 1
    assert len(duplicate_groups[0]) == 2
    # Проверяем, что группа содержит img1 и img2 (порядок не важен)
    group_ids = {img.id for img in duplicate_groups[0]}
    assert group_ids == {1, 2}


def test_find_duplicates_multiple_groups(duplicate_detector, mock_dataset, mock_image):
    # Два дубля: (1,2) и (3,4)
    emb1 = np.array([1.0, 0.0])
    emb2 = np.array([1.0, 0.0])  # дубль 1
    emb3 = np.array([0.0, 1.0])
    emb4 = np.array([0.0, 1.0])  # дубль 2
    img1 = mock_image(1, emb1)
    img2 = mock_image(2, emb2)
    img3 = mock_image(3, emb3)
    img4 = mock_image(4, emb4)
    dataset = mock_dataset([img1, img2, img3, img4])
    threshold = 0.99

    result = duplicate_detector.find_duplicates(dataset, progress_callback=None, cancel_check=None, threshold=threshold)
    duplicate_groups, _ = result
    assert len(duplicate_groups) == 2
    # Каждая группа должна содержать 2 изображения
    sizes = [len(group) for group in duplicate_groups]
    assert sizes == [2, 2]


def test_find_duplicates_threshold_effect(duplicate_detector, mock_dataset, mock_image):
    # Два похожих, но не идентичных вектора. Косинусное сходство между [0.9,0.1] и [0.8,0.2] допустим 0.98?
    # Для простоты используем векторы с известным сходством.
    emb1 = np.array([0.91, 0.09])
    emb2 = np.array([0.89,
                     0.11])  # сходство близко к 0.999? Посчитаем: (0.91*0.89+0.09*0.11)/(sqrt(0.91^2+0.09^2)*sqrt(0.89^2+0.11^2)) ~ (0.8099+0.0099)/(0.914*0.897) ~ 0.8198/0.820 ≈ 0.9998
    # Создаём третий, далёкий
    emb3 = np.array([0.0, 1.0])
    img1 = mock_image(1, emb1)
    img2 = mock_image(2, emb2)
    img3 = mock_image(3, emb3)
    dataset = mock_dataset([img1, img2, img3])

    # Высокий порог (1.0)
    result_high = duplicate_detector.find_duplicates(dataset, progress_callback=None,
                                                     cancel_check=None, threshold=1.0)
    groups_high, _ = result_high
    assert len(groups_high) == 0

    # Пониженный порог (0.95)
    result_low = duplicate_detector.find_duplicates(dataset, progress_callback=None,
                                                    cancel_check=None, threshold=0.95)
    groups_low, _ = result_low
    assert len(groups_low) == 1
    assert len(groups_low[0]) == 2


def test_find_duplicates_empty_dataset(duplicate_detector, mock_dataset):
    dataset = mock_dataset([])
    result = duplicate_detector.find_duplicates(dataset, progress_callback=None, cancel_check=None, threshold=0.95)
    duplicate_groups, returned_dataset = result
    assert duplicate_groups == []
    assert returned_dataset is dataset


def test_find_duplicates_cancel_during_preparation(duplicate_detector, mock_dataset, mock_image):
    img1 = mock_image(1, np.array([1.0, 0.0]))
    dataset = mock_dataset([img1])
    cancel_check = lambda: True  # сразу отмена
    result = duplicate_detector.find_duplicates(dataset, progress_callback=None, cancel_check=cancel_check,
                                                threshold=0.95)
    assert result is None


def test_find_duplicates_cancel_during_graph_building(duplicate_detector, mock_dataset, mock_image):
    # Создаём несколько изображений, чтобы отмена произошла в цикле
    images = [mock_image(i, np.random.rand(2)) for i in range(5)]
    dataset = mock_dataset(images)
    cancel_counter = [0]

    def cancel_check():
        cancel_counter[0] += 1
        return cancel_counter[0] > 2  # отмена после нескольких итераций

    result = duplicate_detector.find_duplicates(dataset, progress_callback=None, cancel_check=cancel_check,
                                                threshold=0.95)
    assert result is None


def test_find_duplicates_progress_callback_called(duplicate_detector, mock_dataset, mock_image):
    emb1 = np.array([1.0, 0.0])
    emb2 = np.array([1.0, 0.0])
    img1 = mock_image(1, emb1)
    img2 = mock_image(2, emb2)
    dataset = mock_dataset([img1, img2])
    progress_calls = []

    def progress_callback(percent, status):
        progress_calls.append((percent, status))

    duplicate_detector.find_duplicates(dataset, progress_callback=progress_callback, cancel_check=None, threshold=0.99)
    # Проверяем, что прогресс вызывался несколько раз (с разными процентами)
    assert len(progress_calls) > 0
    # Проверяем, что последний вызов – 100%
    assert progress_calls[-1][0] == 100
