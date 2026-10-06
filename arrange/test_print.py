"""一時ディレクトリ内で生成・再実行・移行済み記事の保護を検証する。"""
import csv
import io
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout

import yaml
from print import FIELDS, generate


class GenerationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'arrange').mkdir()
        (self.root / '_news/2025').mkdir(parents=True)
        self.legacy = self.root / '_news/2025/old.md'
        self.legacy.write_text('---\nlayout: post\ncategory: LIVE\ndate: 2025-01-01\ntitle: 過去記事\n---\n元の記事\n')
        self.row = dict.fromkeys(FIELDS, '')
        self.row.update(title='テスト "公演" & <ゲスト>', date='2026-11-01', venue='会場',
                        time_start='23:30', url='https://example.com/?a=1&b=2',
                        performer='A & B', streaming_url='https://example.com/live', streaming_price='1,000')

    def save(self, rows):
        with (self.root / 'arrange/lives.csv').open('w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def rows(self):
        with (self.root / 'arrange/lives.csv').open(newline='') as f:
            return list(csv.DictReader(f))

    def run_generator(self, today='2026-10-04'):
        with redirect_stdout(io.StringIO()):
            generate(self.root, today)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def test_new_news_and_rerun(self):
        original = self.legacy.read_bytes()
        self.save([self.row])
        self.run_generator()
        row = self.rows()[0]
        self.assertTrue(row['live_id'])
        self.assertEqual(row['news_date'], '2026-10-04')
        post = next((self.root / '_news/2026').glob('*.md'))
        text = post.read_text()
        meta = yaml.safe_load(text.split('---', 2)[1])
        self.assertEqual(meta['title'], '【11/1】テスト "公演" & <ゲスト>【出演決定】')
        self.assertEqual(meta['date'], '2026-10-04 00:00:00 +0900')
        self.assertIn('&lt;ゲスト&gt;', text)
        self.assertIn('href="https://example.com/live"', text)
        self.assertIn('%26', text)
        with (self.root / 'arrange/output/timetree.csv').open(encoding='utf-8-sig') as f:
            item = next(csv.DictReader(f))
        self.assertEqual(item['終了日時'], '2026-11-02 00:30')
        self.run_generator('2026-10-05')
        self.assertEqual(post.read_text(), text)
        self.assertEqual(len(list(self.root.glob('_news/**/*.md'))), 2)
        self.assertEqual(self.legacy.read_bytes(), original)
        before = self.snapshot()
        self.run_generator('2026-10-06')
        self.assertEqual(self.snapshot(), before)

    def test_timetree_only_new_lives_independent_of_news(self):
        self.save([self.row])
        self.run_generator()
        rows = self.rows()
        rows[0].update(title='既存公演を修正', url='https://example.com/changed')
        self.save(rows + [dict(self.row, title='追加公演', news_date='-')])
        self.run_generator()
        path = self.root / 'arrange/output/timetree.csv'
        with path.open(encoding='utf-8-sig') as f:
            exported = list(csv.DictReader(f))
        self.assertEqual([row['予定タイトル'] for row in exported], ['追加公演'])
        self.assertEqual(len(yaml.safe_load((self.root / '_data/lives.yml').read_text())), 2)
        self.assertIn('既存公演を修正', (self.root / 'arrange/output/newlive.txt').read_text())
        self.run_generator()
        with path.open(encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            self.assertIn('予定タイトル', reader.fieldnames)
            self.assertEqual(list(reader), [])

    def test_readable_filename_and_collision(self):
        self.save([dict(self.row, title='同名公演'),
                   dict(self.row, title='同名公演', time_start='20:00'),
                   dict(self.row, title='同名公演', time_start='20:00', venue='別会場')])
        self.run_generator()
        names = {p.name for p in self.root.glob('_news/2026/*.md')}
        self.assertEqual(names, {'261004_同名公演.md',
                                 '261004_同名公演_20261101_2000.md',
                                 '261004_同名公演_20261101_2000_2.md'})
        self.run_generator()
        self.assertEqual({p.name for p in self.root.glob('_news/2026/*.md')}, names)

    def test_filename_path_characters(self):
        self.save([dict(self.row, title='../特別公演/昼:夜?')])
        self.run_generator()
        self.assertTrue((self.root / '_news/2026/261004__特別公演_昼_夜_.md').exists())

    def test_title_with_front_matter_separator(self):
        self.save([dict(self.row, title='公演---特別編')])
        self.run_generator()
        self.run_generator()
        self.assertEqual(len(list(self.root.glob('_news/2026/*.md'))), 1)

    def test_correction_updates_live_but_preserves_news(self):
        self.save([self.row]); self.run_generator()
        post = next(self.root.glob('_news/2026/*.md')); before = post.read_bytes()
        rows = self.rows()
        rows[0].update(title='変更', date='2026-12-02', venue='新会場', url='https://example.com/new', news_date='2026-10-03')
        self.save(rows); self.run_generator()
        self.assertEqual(post.read_bytes(), before)
        data = yaml.safe_load((self.root / '_data/lives.yml').read_text())
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['venue'], '新会場')
        self.assertEqual(len(list(self.root.glob('_news/2026/*.md'))), 1)

    def test_baseline_and_explicit_date(self):
        self.save([dict(self.row, news_date='-'), dict(self.row, title='新規', news_date='2026-09-30')])
        self.run_generator()
        self.assertEqual(len(list(self.root.glob('_news/2026/*.md'))), 1)
        self.assertTrue(next(self.root.glob('_news/2026/*.md')).name.startswith('260930_'))

    def test_removal_keeps_news(self):
        self.save([self.row, dict(self.row, title='別公演')]); self.run_generator()
        rows = self.rows(); self.save(rows[1:]); self.run_generator()
        self.assertEqual(len(yaml.safe_load((self.root / '_data/lives.yml').read_text())), 1)
        self.assertEqual(len(list(self.root.glob('_news/2026/*.md'))), 2)
        self.save(rows); self.run_generator()
        self.assertEqual(len(list(self.root.glob('_news/2026/*.md'))), 2)

    def test_invalid_input_writes_nothing(self):
        cases = [dict(self.row, date='2026-02-30'), dict(self.row, news_date='2027-01-01'),
                 dict(self.row, live_id='../bad'), dict(self.row, title='{% include bad %}'),
                 dict(self.row, time_start='25:00')]
        for row in cases:
            with self.subTest(row=row):
                self.save([row]); before = self.snapshot()
                with self.assertRaises(ValueError): self.run_generator()
                self.assertEqual(self.snapshot(), before)

    def test_duplicate_id_and_duplicate_performance(self):
        for rows in [[dict(self.row, live_id='same'), dict(self.row, title='別公演', live_id='same')], [self.row, self.row]]:
            self.save(rows); before = self.snapshot()
            with self.assertRaises(ValueError): self.run_generator()
            self.assertEqual(self.snapshot(), before)

    def test_omitted_trailing_optional_columns(self):
        self.save([self.row])
        path = self.root / 'arrange/lives.csv'
        with path.open(newline='') as f:
            records = list(csv.reader(f))
        with path.open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(records[0])
            writer.writerow(records[1][:12])
        self.run_generator()
        self.assertTrue(self.rows()[0]['live_id'])
        self.assertEqual(self.rows()[0]['news_date'], '2026-10-04')

    def test_legacy_headers_and_extra_columns_write_nothing(self):
        path = self.root / 'arrange/lives.csv'
        for headers, values in [(FIELDS[:15], [self.row[k] for k in FIELDS[:15]]),
                                (FIELDS, [self.row[k] for k in FIELDS] + ['extra'])]:
            with path.open('w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerow(values)
            before = self.snapshot()
            with self.assertRaises(ValueError):
                self.run_generator()
            self.assertEqual(self.snapshot(), before)

    def test_malformed_csv(self):
        self.save([self.row])
        with (self.root / 'arrange/lives.csv').open('a') as f: f.write('broken,row\n')
        before = self.snapshot()
        with self.assertRaises(ValueError): self.run_generator()
        self.assertEqual(self.snapshot(), before)

    def test_recovery_after_article_written_before_yaml(self):
        self.save([self.row]); self.run_generator()
        (self.root / '_data/lives.yml').unlink()
        self.run_generator()
        self.assertEqual(len(list(self.root.glob('_news/2026/*.md'))), 1)
        self.assertTrue((self.root / '_data/lives.yml').exists())


if __name__ == '__main__':
    unittest.main()
