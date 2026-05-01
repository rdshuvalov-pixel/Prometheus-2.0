from backend.pipeline.normalize.role import is_product_title
from backend.pipeline.normalize.seniority import detect_seniority
from backend.pipeline.normalize.work_format import detect_work_format


def test_product_title_pm():
    assert is_product_title("Senior Product Manager", "")


def test_non_product_pm_title():
    assert not is_product_title("Project Manager", "")


def test_seniority():
    assert detect_seniority("Junior PM", "") == "junior"
    assert detect_seniority("Senior Product Manager", "") == "senior"


def test_work_format():
    assert detect_work_format("Fully remote EU") == "remote"
