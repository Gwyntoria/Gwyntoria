import unittest

from scripts.update_recent import (
    COLLECTIONS,
    extract_latest_articles,
    render_entries,
    update_readme,
)


ALBUM_PAGE = """
<script>
var cgiData = {
  articleList: [
    {
      title: '2025年度书单',
      create_time: '1764979200',
      url: 'http://mp.weixin.qq.com/s?__biz=example&amp;mid=2#rd',
    },
    {
      title: '2024年度书单',
      url: 'http://mp.weixin.qq.com/s?__biz=example&amp;mid=1#rd',
    },
    {
      title: '2023年度书单',
      url: 'http://mp.weixin.qq.com/s?mid=3#rd',
    },
    {
      title: '2022年度书单',
      url: 'http://mp.weixin.qq.com/s?mid=4#rd',
    },
    {
      title: '2021年度书单',
      url: 'http://mp.weixin.qq.com/s?mid=5#rd',
    },
    {
      title: '2020年度书单',
      url: 'http://mp.weixin.qq.com/s?mid=6#rd',
    }
  ],
  continue_flag: '0' * 1,
};
</script>
"""


class UpdateRecentTest(unittest.TestCase):
    def test_extracts_five_latest_articles_and_normalizes_urls(self) -> None:
        articles = extract_latest_articles(ALBUM_PAGE)

        self.assertEqual(len(articles), 5)
        self.assertEqual(articles[0][0], "2025年度书单")
        self.assertEqual(
            articles[0][1],
            "https://mp.weixin.qq.com/s?__biz=example&mid=2",
        )
        self.assertEqual(articles[-1][0], "2021年度书单")

    def test_updates_only_marked_block(self) -> None:
        markers = COLLECTIONS["meditations"]
        original = (
            "## Recently\n\n"
            f"{markers['start_marker']}\nold entry\n{markers['end_marker']}\n"
            "<!-- ANNUAL_BOOK_LIST:START -->\nannual entry\n"
            "<!-- ANNUAL_BOOK_LIST:END -->\n"
            "- Existing entry\n"
        )
        entries = render_entries(
            [
                ("2025年度书单", "https://mp.weixin.qq.com/s?mid=2"),
                ("2024年度书单", "https://mp.weixin.qq.com/s?mid=1"),
            ]
        )

        updated = update_readme(
            original,
            entries,
            markers["start_marker"],
            markers["end_marker"],
        )

        self.assertIn(entries, updated)
        self.assertIn("- Existing entry", updated)
        self.assertIn("annual entry", updated)
        self.assertNotIn("old entry", updated)

    def test_rejects_too_few_articles(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected at least 7"):
            extract_latest_articles(ALBUM_PAGE, limit=7)

    def test_rejects_missing_markers(self) -> None:
        markers = COLLECTIONS["meditations"]
        with self.assertRaisesRegex(ValueError, "exactly one"):
            update_readme(
                "## Recently\n",
                "new entry",
                markers["start_marker"],
                markers["end_marker"],
            )

    def test_collection_markers_are_unique(self) -> None:
        marker_pairs = {
            (collection["start_marker"], collection["end_marker"])
            for collection in COLLECTIONS.values()
        }

        self.assertEqual(len(marker_pairs), len(COLLECTIONS))


if __name__ == "__main__":
    unittest.main()
