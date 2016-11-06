from test.basetestcase import TestCase
from pagerank import get_page_rank_scores


class PageRankTestCase(TestCase):

    def test_get_page_rank_scores(self):
        result = get_page_rank_scores([(1, 2), (2, 4), (4, 3)])
        self.assertEqual(result, {
            1: 0.05000000000000001,
            2: 0.092500000000000027,
            4: 0.12862500000000002,
        })

        result = get_page_rank_scores(
            [(1, 2), (2, 4), (4, 3), (3, 1), (3, 2)],
        )
        self.assertEqual(result, {
            1: 0.15667918572028511,
            2: 0.28985649358252741,
            3: 0.2791899914185817,
            4: 0.2838780195451483,
        })
