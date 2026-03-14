from app.services.compliance_service import DISCLAIMER_TEXT, ensure_disclaimer
from app.services.internal_link_service import append_internal_links


def test_disclaimer_is_appended_once() -> None:
    content = '<p>Hello</p>'
    with_disclaimer = ensure_disclaimer(content)
    assert DISCLAIMER_TEXT in with_disclaimer

    second_pass = ensure_disclaimer(with_disclaimer)
    assert second_pass.count(DISCLAIMER_TEXT) == 1


def test_internal_links_are_added() -> None:
    html = append_internal_links('<h1>Article</h1>')
    assert 'Internal Links' in html
    assert 'Wellnest Connect' in html
    assert 'https://connect.wellnestgroup.life/' in html
    assert 'Wellnest Horizons' in html
    assert 'https://horizons.wellnestgroup.life/' in html
