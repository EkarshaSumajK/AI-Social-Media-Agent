HARD_CODED_INTERNAL_LINKS: tuple[tuple[str, str], ...] = (
    ('Wellnest Connect', 'https://connect.wellnestgroup.life/'),
    ('Wellnest Horizons', 'https://horizons.wellnestgroup.life/'),
)


def build_internal_links_block() -> str:
    links = '\n'.join(
        f'<li><a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a></li>'
        for label, url in HARD_CODED_INTERNAL_LINKS
    )
    return (
        '<section>'
        '<h3>Internal Links</h3>'
        f'<ul>{links}</ul>'
        '</section>'
    )


def append_internal_links(content_html: str) -> str:
    block = build_internal_links_block()
    return f'{content_html}\n\n{block}'
