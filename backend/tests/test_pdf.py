from backend.app.services.pdf import build_filename_base, sanitize_filename_part


def test_sanitize_filename_part_removes_unsafe_characters():
    assert sanitize_filename_part("Tarun Kumar") == "Tarun_Kumar"
    assert (
        sanitize_filename_part("Java Developer / Backend") == "Java_Developer_Backend"
    )
    assert sanitize_filename_part("Meta: Platforms?") == "Meta_Platforms"


def test_build_filename_base_uses_name_company_role():
    assert (
        build_filename_base("Tarun Kumar", "Meta Platforms", "Java Developer")
        == "Tarun_Kumar_Meta_Platforms_Java_Developer"
    )


def test_sanitize_filename_part_long_name_retains_length():
    long_name = "Tarun_Mannava_Google_Software_Engineer_AI_Machine_Learning_PhD_Early_Career_2027_Start"
    assert len(long_name) > 80
    assert sanitize_filename_part(long_name) == long_name

